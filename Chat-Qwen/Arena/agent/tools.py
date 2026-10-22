"""Инструменты (tools) агента — единственный способ, которым он трогает систему.

Каждый инструмент:
  * имеет JSON-схему (её видит LLM / MCP-клиент);
  * возвращает dict (он же уходит обратно модели);
  * для командных инструментов проходит через policy.guard().

Регистр TOOLS используется и CLI-чатом, и MCP-сервером, и LLM-циклом.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from .config import Config
from .policy import Auditor, Risk, classify, guard

# --------------------------------------------------------------------------- #
#  низкоуровневый запуск
# --------------------------------------------------------------------------- #


@dataclass
class ExecResult:
    command: str
    ok: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    risk: str | None = None
    denied_reason: str | None = None


def run_command(command: str, cfg: Config, *, approve: Callable[[str, str], bool] | None = None,
                force_risk: Risk | None = None) -> ExecResult:
    """Единственная точка запуска внешних процессов. shell=False всегда."""
    started = time.monotonic()
    verdict = classify(command)
    risk = force_risk or verdict.risk

    if verdict.risk is None and force_risk is None:
        return ExecResult(command, False, -1, "", f"отклонено: {verdict.reason}", 0)

    ok_to_run, why = guard(verdict, cfg.policy.mode, cfg.policy.allow_dangerous)
    if not ok_to_run and approve is not None and verdict.risk is Risk.WRITE:
        ok_to_run = approve(command, verdict.reason)
        why = "подтверждено пользователем" if ok_to_run else "отклонено пользователем"

    if not ok_to_run:
        return ExecResult(command, False, -1, "", why, 0,
                          risk=risk.value if risk else None, denied_reason=why)

    try:
        proc = subprocess.run(  # noqa: S603 — аргументы разобраны shlex, shell=False
            verdict.parsed,
            capture_output=True,
            text=True,
            timeout=cfg.policy.command_timeout,
            env={**os.environ, "SYSTEMD_COLORS": "0", "LC_ALL": "C.UTF-8"},
        )
        stdout, stderr = _truncate(proc.stdout, cfg), _truncate(proc.stderr, cfg)
        res = ExecResult(command, proc.returncode == 0, proc.returncode, stdout, stderr,
                         int((time.monotonic() - started) * 1000),
                         risk=risk.value if risk else None)
    except FileNotFoundError:
        res = ExecResult(command, False, 127, "", "программа не найдена", 0,
                         risk=risk.value if risk else None)
    except subprocess.TimeoutExpired:
        res = ExecResult(command, False, -2, "", f"таймаут {cfg.policy.command_timeout}с", 0,
                         risk=risk.value if risk else None)

    Auditor(cfg.policy.audit_log).write(
        tool="run_command", command=command, risk=res.risk, ok=res.ok,
        exit_code=res.exit_code, denied=res.denied_reason,
    )
    return res


def _truncate(text: str, cfg: Config) -> str:
    limit = cfg.policy.max_output_bytes
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... [обрезано, всего {len(text)} байт]"


# --------------------------------------------------------------------------- #
#  журнал systemd
# --------------------------------------------------------------------------- #

PRIORITY_NAMES = {"0": "emerg", "1": "alert", "2": "crit", "3": "err", "4": "warning",
                  "5": "notice", "6": "info", "7": "debug"}


def journal_errors(cfg: Config, unit: str | None = None, since: str = "-1h",
                   limit: int = 200, priority: str = "err",
                   approve=None) -> dict[str, Any]:
    """Ошибки из журнала systemd, сгруппированные по «шаблону» сообщения.

    Группировка важна: модели не нужно 200 одинаковых строк, ей нужны 5
    уникальных проблем и их количество.
    """
    if not shutil.which("journalctl"):
        return {"error": "journalctl не найден (не systemd-система?)"}
    parts = ["journalctl", "--no-pager", "-o", "json", "-p", priority]
    if unit:
        parts += ["-u", unit]
    parts += ["--since", since, "-n", str(max(1, min(limit, 2000)))]
    command = " ".join(parts)

    res = run_command(command, cfg, approve=approve, force_risk=Risk.READ)
    if res.denied_reason:
        return {"error": res.denied_reason}
    if res.exit_code != 0 and not res.stdout.strip():
        return {"error": res.stderr.strip() or f"journalctl вернул код {res.exit_code}"}

    events, parse_errors = [], 0
    for line in res.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError:
            parse_errors += 1
            continue
        events.append({
            "ts": _ts(raw.get("__REALTIME_TIMESTAMP")),
            "unit": raw.get("_SYSTEMD_UNIT") or raw.get("SYSLOG_IDENTIFIER") or "?",
            "priority": PRIORITY_NAMES.get(str(raw.get("PRIORITY")), str(raw.get("PRIORITY"))),
            "pid": raw.get("_PID"),
            "message": _clean(raw.get("MESSAGE", "")),
        })

    return {
        "since": since,
        "unit": unit,
        "total_events": len(events),
        "groups": _cluster(events),
        "unparsed_lines": parse_errors,
    }


def _clean(message: Any) -> str:
    if isinstance(message, list):  # бинарные сообщения journald отдаёт списком байт
        try:
            message = bytes(message).decode("utf-8", "replace")
        except Exception:
            message = str(message)
    text = str(message)
    text = re.sub(r"\b0x[0-9a-fA-F]{6,}\b", "<addr>", text)
    text = re.sub(r"\b[0-9a-f]{8,}-[0-9a-f\-]{8,}\b", "<uuid>", text)
    text = re.sub(r"\b\d{2,}\b", "<n>", text)
    return text.strip()[:400]


def _cluster(events: list[dict]) -> list[dict]:
    buckets: dict[tuple, dict] = {}
    for ev in events:
        key = (ev["unit"], ev["message"])
        b = buckets.setdefault(key, {"unit": ev["unit"], "message": ev["message"],
                                     "count": 0, "first": ev["ts"], "last": ev["ts"],
                                     "priorities": set()})
        b["count"] += 1
        b["last"] = ev["ts"]
        b["priorities"].add(ev["priority"])
    out = []
    for b in buckets.values():
        b["priorities"] = sorted(b["priorities"])
        out.append(b)
    out.sort(key=lambda x: (-x["count"], x["unit"]))
    return out[:25]


def _ts(micro: Any) -> str:
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(micro) / 1_000_000))
    except Exception:
        return "?"


# --------------------------------------------------------------------------- #
#  простые обёртки, которые экономят модели целый раунд
# --------------------------------------------------------------------------- #


def failed_units(cfg: Config, approve=None) -> dict[str, Any]:
    res = run_command("systemctl list-units --state=failed --no-pager --plain --no-legend",
                      cfg, approve=approve, force_risk=Risk.READ)
    if res.denied_reason:
        return {"error": res.denied_reason}
    lines = [ln.strip() for ln in res.stdout.splitlines() if ln.strip()]
    units = [{"unit": ln.split()[0], "raw": ln} for ln in lines if ln.endswith(("failed", "loaded")) or "failed" in ln]
    return {"failed_count": len(units), "units": units,
            "hint": "для каждой службы: systemctl status <unit> и journal_errors(unit=<unit>)"}


def disk_usage(cfg: Config, approve=None) -> dict[str, Any]:
    res = run_command("df -h -x tmpfs -x devtmpfs", cfg, approve=approve, force_risk=Risk.READ)
    return {"output": res.stdout or res.stderr, "exit_code": res.exit_code}


def memory_usage(cfg: Config, approve=None) -> dict[str, Any]:
    res = run_command("free -h", cfg, approve=approve, force_risk=Risk.READ)
    return {"output": res.stdout or res.stderr, "exit_code": res.exit_code}


def top_processes(cfg: Config, sort_by: str = "cpu", count: int = 10, approve=None) -> dict[str, Any]:
    key = "--sort=-%mem" if sort_by == "mem" else "--sort=-%cpu"
    res = run_command(f"ps -eo pid,ppid,user,pcpu,pmem,etime,comm {key}", cfg,
                      approve=approve, force_risk=Risk.READ)
    lines = res.stdout.splitlines()
    return {"sort_by": sort_by, "processes": lines[: max(2, min(count, 50))]}


def unit_status(cfg: Config, unit: str, approve=None) -> dict[str, Any]:
    if not re.fullmatch(r"[A-Za-z0-9@._:\\-]+", unit):
        return {"error": "некорректное имя юнита"}
    res = run_command(f"systemctl status {unit} --no-pager -l", cfg,
                      approve=approve, force_risk=Risk.READ)
    return {"unit": unit, "exit_code": res.exit_code, "output": res.stdout or res.stderr}


def tail_log_file(cfg: Config, path: str, lines: int = 100, approve=None) -> dict[str, Any]:
    p = Path(path)
    if not str(p.resolve()).startswith(("/var/log", "/var/crash")):
        return {"error": "разрешено читать только файлы в /var/log и /var/crash"}
    if not p.is_file():
        return {"error": f"нет такого файла: {path}"}
    res = run_command(f"tail -n {max(1, min(int(lines), 2000))} {path}", cfg,
                      approve=approve, force_risk=Risk.READ)
    return {"path": path, "output": res.stdout or res.stderr, "exit_code": res.exit_code}


def run_shell_command(cfg: Config, command: str, approve=None) -> dict[str, Any]:
    """Произвольная команда — но только из белого списка policy.py."""
    res = run_command(command, cfg, approve=approve)
    return asdict(res)


# --------------------------------------------------------------------------- #
#  реестр инструментов: схема + обработчик
# --------------------------------------------------------------------------- #

TOOLS: dict[str, dict[str, Any]] = {
    "journal_errors": {
        "fn": journal_errors,
        "description": "Ошибки (и выше) из журнала systemd, сгруппированные по шаблону "
                       "сообщения с подсчётом повторов. Основной инструмент диагностики.",
        "parameters": {
            "type": "object",
            "properties": {
                "unit": {"type": "string", "description": "служба, напр. nginx.service (опционально)"},
                "since": {"type": "string", "description": "период: -1h, -30m, 'today', '2026-10-20'"},
                "limit": {"type": "integer", "description": "сколько записей прочитать (<=2000)"},
                "priority": {"type": "string", "enum": ["emerg", "alert", "crit", "err", "warning"],
                             "description": "минимальный уровень важности"},
            },
        },
    },
    "failed_units": {
        "fn": failed_units,
        "description": "Список юнитов systemd в состоянии failed.",
        "parameters": {"type": "object", "properties": {}},
    },
    "unit_status": {
        "fn": unit_status,
        "description": "Подробный статус службы: состояние, последние строки лога, кем запущена.",
        "parameters": {"type": "object", "properties": {"unit": {"type": "string"}},
                       "required": ["unit"]},
    },
    "disk_usage": {"fn": disk_usage, "description": "Занятость файловых систем (df -h).",
                   "parameters": {"type": "object", "properties": {}}},
    "memory_usage": {"fn": memory_usage, "description": "Память и swap (free -h).",
                     "parameters": {"type": "object", "properties": {}}},
    "top_processes": {
        "fn": top_processes,
        "description": "Топ процессов по CPU или памяти.",
        "parameters": {"type": "object", "properties": {
            "sort_by": {"type": "string", "enum": ["cpu", "mem"]},
            "count": {"type": "integer"}}},
    },
    "tail_log_file": {
        "fn": tail_log_file,
        "description": "Последние строки текстового лог-файла в /var/log (nginx, syslog, auth.log).",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string"}, "lines": {"type": "integer"}}, "required": ["path"]},
    },
    "run_shell_command": {
        "fn": run_shell_command,
        "description": "Выполнить одну системную команду. Разрешено только то, что есть в "
                       "белом списке политики; команды с пайпами отклоняются.",
        "parameters": {"type": "object", "properties": {
            "command": {"type": "string", "description": "напр. 'systemctl restart nginx'"}},
            "required": ["command"]},
        "requires_approval": True,
    },
}


def openai_tool_schemas() -> list[dict[str, Any]]:
    return [{"type": "function",
             "function": {"name": name, "description": spec["description"],
                          "parameters": spec["parameters"]}}
            for name, spec in TOOLS.items()]


def call_tool(name: str, arguments: dict[str, Any], cfg: Config, approve=None) -> dict[str, Any]:
    spec = TOOLS.get(name)
    if spec is None:
        return {"error": f"неизвестный инструмент: {name}"}
    fn: Callable = spec["fn"]
    try:
        return fn(cfg, approve=approve, **arguments)
    except TypeError as exc:
        return {"error": f"неверные аргументы для {name}: {exc}"}
    except Exception as exc:  # инструмент не должен ронять агента
        return {"error": f"{type(exc).__name__}: {exc}"}
