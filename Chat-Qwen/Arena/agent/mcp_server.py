"""MCP-сервер (Model Context Protocol) поверх stdio.

Зачем: MCP — это «стандартный разъём», через который любой MCP-клиент
(Claude Desktop, IDE, свой чат) видит ваши инструменты как обычные tools.
Тогда ваш агент = MCP-сервер над системой, а UI/чат можно не писать вообще.

Запуск:  python3 -m sysagent.mcp_server --mode readonly
Подключение в claude_desktop_config.json:
  {"mcpServers": {"sysagent": {"command": "python3",
    "args": ["-m", "sysagent.mcp_server", "--mode", "readonly"]}}}
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .config import Config
from .tools import TOOLS, call_tool

PROTOCOL_VERSION = "2024-11-05"


def _tool_definitions() -> list[dict[str, Any]]:
    return [
        {"name": name,
         "description": spec["description"],
         "inputSchema": spec["parameters"] or {"type": "object", "properties": {}}}
        for name, spec in TOOLS.items()
    ]


def _handle(request: dict, cfg: Config) -> dict | None:
    method = request.get("method")
    req_id = request.get("id")
    params = request.get("params") or {}

    if method == "initialize":
        result = {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "sysagent", "version": "0.1.0"},
            "instructions": "Инструменты администрирования Linux. "
                            "Сначала диагностика (journal_errors, failed_units), потом действия.",
        }
    elif method == "tools/list":
        result = {"tools": _tool_definitions()}
    elif method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments") or {}
        # в MCP нет интерактивного подтверждения -> работает только policy (readonly/auto)
        payload = call_tool(name, args, cfg, approve=None)
        result = {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}],
                  "isError": "error" in payload}
    elif method == "ping":
        result = {}
    elif method is not None and method.startswith("notifications/"):
        return None  # уведомления не требуют ответа
    else:
        return {"jsonrpc": "2.0", "id": req_id,
                "error": {"code": -32601, "message": f"method not found: {method}"}}

    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sysagent-mcp")
    parser.add_argument("--config")
    parser.add_argument("--mode", default="readonly", choices=["readonly", "ask", "auto"])
    args = parser.parse_args(argv)

    cfg = Config.load(args.config)
    cfg.policy.mode = "readonly" if args.mode == "readonly" else args.mode

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            print(json.dumps({"jsonrpc": "2.0", "id": None,
                              "error": {"code": -32700, "message": "parse error"}}),
                  flush=True)
            continue
        response = _handle(request, cfg)
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
