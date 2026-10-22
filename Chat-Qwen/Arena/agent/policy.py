"""Политика безопасности: классификация команд + подтверждение + аудит.

Это самая важная часть агента. LLM ошибается, поэтому решение о запуске
принимает НЕ модель, а этот модуль:

  read       — можно запускать сразу
  write      — изменяет систему -> подтверждение (в режиме ask)
  dangerous  — по умолчанию запрещено навсегда (allow_dangerous = false)
  None       — команда неизвестна -> запрещено

Правила — упорядоченный список регулярных выражений, первое совпадение
побеждает. Список легко расширять под свой парк серверов.
"""

from __future__ import annotations

import getpass
import json
import re
import shlex
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Risk(str, Enum):
    READ = "read"
    WRITE = "write"
    DANGEROUS = "dangerous"


# (регулярка, риск, пояснение)
RULES: list[tuple[str, Risk, str]] = [
    # --- то, что не должен делать никакой агент сам ------------------------
    (r"\b(rm|shred|unlink|wipefs|mkfs\S*|fdisk|sfdisk|parted|dd)\b", Risk.DANGEROUS,
     "разрушение данных / разметки диска"),
    (r"^(reboot|shutdown|poweroff|halt|kexec)\b", Risk.DANGEROUS, "перезагрузка/выключение"),
    (r"^systemctl\s+(poweroff|reboot|halt|kexec|rescue|emergency)", Risk.DANGEROUS,
     "смена режима работы системы"),
    (r"^(useradd|userdel|usermod|groupadd|groupdel|gpasswd|chpasswd|visudo)\b",
     Risk.DANGEROUS, "изменение пользователей/прав"),
    (r"^passwd\b", Risk.DANGEROUS, "смена пароля"),
    (r"^(iptables|ip6tables|nft|ufw|firewall-cmd)\b", Risk.DANGEROUS,
     "правила файрвола — можно потерять доступ к серверу"),
    (r"^crontab\s+-r", Risk.DANGEROUS, "удаление crontab"),
    (r"^chmod\s+(-R\s+)?[0-7]{3,4}\s+/(\s|$)", Risk.DANGEROUS, "chmod на корень"),
    (r"^chown\s+(-R\s+)?\S+\s+/(\s|$)", Risk.DANGEROUS, "chown на корень"),
    (r"^sudo\b", Risk.DANGEROUS, "вложенный sudo — агент сам должен иметь нужные права"),
    (r"^(curl|wget)\b", Risk.DANGEROUS, "загрузка/утечка данных по сети"),
    (r"^docker\s+(rm|rmi|prune|system\s+prune)\b", Risk.DANGEROUS, "удаление контейнеров"),
    (r"^(init|telinit)\s+[06]", Risk.DANGEROUS, "смена runlevel"),

    # --- изменения состояния ------------------------------------------------
    (r"^systemctl\s+(start|stop|restart|reload|reload-or-restart|try-restart|"
     r"enable|disable|mask|unmask|daemon-reload|reset-failed|kill)\b", Risk.WRITE,
     "управление службой systemd"),
    (r"^service\s+\S+\s+(start|stop|restart|reload)\b", Risk.WRITE, "управление службой"),
    (r"^journalctl\b.*--(vacuum-\S+|rotate|flush)", Risk.WRITE, "обслуживание журнала"),
    (r"^(apt|apt-get|dnf|yum|zypper|pacman|apk)\s+(install|remove|purge|upgrade|"
     r"update|autoremove|dist-upgrade)\b", Risk.WRITE, "установка/удаление пакетов"),
    (r"^(kill|pkill|killall)\b", Risk.WRITE, "завершение процессов"),
    (r"^docker\s+(start|stop|restart)\b", Risk.WRITE, "управление контейнером"),
    (r"^systemd-run\b", Risk.WRITE, "запуск юнита"),
    (r"^truncate\b", Risk.WRITE, "обрезка файла"),
    (r"^loginctl\s+(terminate|kill)", Risk.WRITE, "завершение сессий"),

    # --- безопасное чтение --------------------------------------------------
    (r"^systemctl\s+(status|list-units|list-unit-files|list-timers|list-sockets|"
     r"show|is-active|is-enabled|is-failed|cat|get-default)\b", Risk.READ, "чтение"),
    (r"^journalctl\b", Risk.READ, "чтение журнала"),
    (r"^(dmesg|last|lastb|who|w|uptime|uname|lscpu|lsblk|lsmem|free|vmstat|iostat|"
     r"mpstat|nproc|hostnamectl|timedatectl|locale|date)\b", Risk.READ, "чтение"),
    (r"^(ps|pstree|pgrep)\b", Risk.READ, "чтение процессов"),
    (r"^(df|du)\b", Risk.READ, "использование диска"),
    (r"^(ss|netstat|ip\s+(a|addr|route|link)|hostname)\b", Risk.READ, "сеть: чтение"),
    (r"^(ping|dig|host|nslookup|traceroute)\b", Risk.READ, "диагностика сети"),
    (r"^(cat|tail|head|less|grep|zgrep|wc|stat|file|ls|find)\b", Risk.READ,
     "чтение файлов (проверяется путь)"),
    (r"^(sensors|smartctl\s+-[aA]|nvme\s+list)\b", Risk.READ, "железо"),
    (r"^(nvidia-smi|sestatus|getenforce|aa-status)\b", Risk.READ, "чтение состояния"),
]

COMPILED = [(re.compile(rx), risk, why) for rx, risk, why in RULES]

# символы, которые ломают «одна команда = одна программа»
SHELL_META = set(";|&$`><\n")


@dataclass
class Verdict:
    risk: Risk | None
    reason: str
    parsed: list[str] | None = None

    @property
    def allowed_automatically(self) -> bool:
        return self.risk is Risk.READ


def classify(command: str) -> Verdict:
    """Определить риск команды. Ничего не выполняет."""
    command = " ".join(command.strip().split())
    if not command:
        return Verdict(None, "пустая команда")

    if any(ch in SHELL_META for ch in command):
        return Verdict(None, "запрещены shell-операторы (; | && > $ `) — "
                             "передавайте одну команду без пайпов")

    for rx, risk, why in COMPILED:
        if rx.search(command):
            if risk is Risk.READ and not _read_paths_look_safe(command):
                return Verdict(None, "чтение файлов разрешено только из /var/log, /etc/sysagent "
                                     "и /proc")
            try:
                parsed = shlex.split(command)
            except ValueError as exc:
                return Verdict(None, f"не удалось разобрать команду: {exc}")
            return Verdict(risk, why, parsed)

    return Verdict(None, "команда не в белом списке политики (policy.py). "
                         "Добавьте правило осознанно, если она действительно нужна")


SAFE_READ_PREFIXES = ("/var/log", "/var/crash", "/proc", "/sys", "/etc/sysagent", "/tmp/sysagent")


def _read_paths_look_safe(command: str) -> bool:
    """Разрешаем читать файлы только из предсказуемых каталогов."""
    try:
        tokens = shlex.split(command)
    except ValueError:
        return False
    for token in tokens[1:]:
        if token.startswith("-"):
            continue
        if token.startswith("/") and not token.startswith(SAFE_READ_PREFIXES):
            return False
        if ".." in token:
            return False
    return True


class Auditor:
    """Журнал всех действий агента — отдельно от системного лога."""

    def __init__(self, path: Path):
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, **fields) -> None:
        record = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "user": _safe_user(),
            **fields,
        }
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def _safe_user() -> str:
    try:
        return getpass.getuser()
    except Exception:
        return "unknown"


def needs_confirmation(verdict: Verdict, mode: str, allow_dangerous: bool) -> bool:
    if verdict.risk is Risk.READ:
        return False
    if verdict.risk is Risk.DANGEROUS:
        return not allow_dangerous  # вызов вернёт отказ, см. guard()
    if mode == "readonly":
        return True  # будет отклонено
    return mode == "ask"


def guard(verdict: Verdict, mode: str, allow_dangerous: bool) -> tuple[bool, str]:
    """Финальное решение: можно ли выполнять без интерактивного подтверждения."""
    if verdict.risk is None:
        return False, f"запрещено: {verdict.reason}"
    if verdict.risk is Risk.DANGEROUS and not allow_dangerous:
        return False, f"запрещено (опасно: {verdict.reason})"
    if verdict.risk is Risk.WRITE and mode == "readonly":
        return False, "режим readonly: изменения запрещены"
    if verdict.risk is Risk.WRITE and mode == "ask":
        return False, "нужно подтверждение пользователя"
    return True, "разрешено"
