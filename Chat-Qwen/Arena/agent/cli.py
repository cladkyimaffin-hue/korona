"""CLI-интерфейс: интерактивный чат + быстрые слэш-команды без LLM."""

from __future__ import annotations

import argparse
import json
import sys

from .config import Config
from .llm import LLMError, describe_tools, run_agent_turn
from .tools import call_tool

BANNER = """\
sysagent — локальный агент администрирования Linux
  /logs [unit]   ошибки журнала (сгруппированные)
  /failed        упавшие юниты
  /status UNIT   статус службы
  /disk /mem /top
  /run CMD       выполнить команду (через политику)
  /tools         список инструментов
  /mode          показать режим политики
  /help /quit
Любой другой текст уходит в LLM (если задан ключ)."""


def _approve(command: str, reason: str) -> bool:
    print(f"\n  ⚠️  агент хочет выполнить: {command}\n     причина: {reason}")
    try:
        return input("     выполнить? [y/N] ").strip().lower() in {"y", "yes", "д", "да"}
    except (EOFError, KeyboardInterrupt):
        return False


def _print(payload) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def handle_slash(line: str, cfg: Config) -> bool:
    """Возвращает False, если пора выходить."""
    parts = line.split(maxsplit=1)
    cmd = parts[0]
    arg = parts[1].strip() if len(parts) > 1 else ""

    if cmd in {"/quit", "/exit", "/q"}:
        return False
    if cmd == "/help":
        print(BANNER)
    elif cmd == "/tools":
        print(describe_tools())
    elif cmd == "/mode":
        print(f"policy.mode={cfg.policy.mode} allow_dangerous={cfg.policy.allow_dangerous} "
              f"audit={cfg.policy.audit_log} llm={cfg.llm.model} "
              f"key={'да' if cfg.llm.api_key else 'нет'}")
    elif cmd == "/logs":
        unit = arg or None
        _print(call_tool("journal_errors", {"unit": unit} if unit else {}, cfg, approve=_approve))
    elif cmd == "/failed":
        _print(call_tool("failed_units", {}, cfg, approve=_approve))
    elif cmd == "/status":
        if not arg:
            print("укажите юнит: /status nginx.service")
        else:
            _print(call_tool("unit_status", {"unit": arg}, cfg, approve=_approve))
    elif cmd == "/disk":
        _print(call_tool("disk_usage", {}, cfg, approve=_approve))
    elif cmd == "/mem":
        _print(call_tool("memory_usage", {}, cfg, approve=_approve))
    elif cmd == "/top":
        _print(call_tool("top_processes", {"sort_by": "cpu", "count": 8}, cfg, approve=_approve))
    elif cmd == "/run":
        if not arg:
            print("укажите команду: /run systemctl status nginx")
        else:
            _print(call_tool("run_shell_command", {"command": arg}, cfg, approve=_approve))
    else:
        print(f"неизвестная команда {cmd}, /help")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sysagent", description="Локальный агент администрирования")
    parser.add_argument("--config", help="путь к config.toml")
    parser.add_argument("--mode", choices=["readonly", "ask", "auto"], help="переопределить режим")
    parser.add_argument("--once", metavar="TEXT", help="выполнить один запрос и выйти")
    parser.add_argument("--tool", metavar="NAME", help="вызвать инструмент напрямую")
    parser.add_argument("--json", metavar="ARGS", default="{}", help="JSON-аргументы для --tool")
    args = parser.parse_args(argv)

    cfg = Config.load(args.config)
    if args.mode:
        cfg.policy.mode = args.mode

    if args.tool:
        _print(call_tool(args.tool, json.loads(args.json), cfg, approve=_approve))
        return 0

    if args.once:
        history: list[dict] = []
        try:
            print(run_agent_turn(cfg, history, args.once, approve=_approve))
        except LLMError as exc:
            print(f"LLM недоступен: {exc}", file=sys.stderr)
            return 2
        return 0

    print(BANNER)
    history = []
    while True:
        try:
            line = input("\nsysagent> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not line:
            continue
        if line.startswith("/"):
            if not handle_slash(line, cfg):
                return 0
            continue
        if not cfg.llm.api_key:
            print("LLM-ключ не задан, работают только слэш-команды. "
                  f"export {cfg.llm.api_key_env}=...")
            continue
        try:
            print(run_agent_turn(cfg, history, line, approve=_approve))
        except LLMError as exc:
            print(f"LLM недоступен: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
