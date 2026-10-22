"""Режим наблюдения: периодически смотрит журнал и сообщает о новых ошибках.

Это «дежурный» слой. Он принципиально read-only: ничего не перезапускает сам.
Автодействия без человека — источник инцидентов, включайте только после того,
как наберёте статистику и добавите чёткие правила (см. README, «Этап 4»).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

from .config import Config
from .tools import journal_errors

STATE = Path("~/.local/state/sysagent/watch-state.json").expanduser()


def load_state() -> set[str]:
    if STATE.is_file():
        try:
            return set(json.loads(STATE.read_text(encoding="utf-8"))["seen"])
        except (json.JSONDecodeError, KeyError):
            return set()
    return set()


def save_state(seen: set[str]) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({"seen": sorted(seen)[-5000:]}), encoding="utf-8")


def notify(title: str, body: str) -> None:
    """Уведомление: в системный журнал (его увидят любые мониторинги) + stderr."""
    message = f"{title}: {body}"
    print(message, flush=True)
    if not sys.stdout.isatty():
        try:
            subprocess.run(["systemd-cat", "-t", "sysagent", "-p", "warning"],
                           input=message, text=True, timeout=5, check=False)  # noqa: S603
        except (FileNotFoundError, subprocess.SubprocessError):
            pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sysagent-watch")
    parser.add_argument("--config")
    parser.add_argument("--interval", type=int, default=60, help="период опроса, сек")
    parser.add_argument("--since", default="-2min", help="окно журнала за цикл")
    args = parser.parse_args(argv)

    cfg = Config.load(args.config)
    cfg.policy.mode = "readonly"  # дежурный контур никогда не меняет систему

    seen = load_state()
    print(f"sysagent-watch: интервал {args.interval}s, окно {args.since}, "
          f"audit={cfg.policy.audit_log}", flush=True)
    while True:
        try:
            report = journal_errors(cfg, since=args.since, limit=500)
            for group in report.get("groups", []):
                key = hashlib.sha256(
                    f"{group['unit']}|{group['message']}".encode()).hexdigest()[:16]
                if key in seen:
                    continue
                seen.add(key)
                notify("новая ошибка",
                       f"[{group['unit']}] x{group['count']} {group['message'][:200]}")
            save_state(seen)
        except KeyboardInterrupt:
            return 0
        except Exception as exc:  # дежурный цикл не должен падать
            print(f"watch error: {type(exc).__name__}: {exc}", flush=True)
        time.sleep(max(10, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
