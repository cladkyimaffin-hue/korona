"""Конфигурация агента: читается из TOML (stdlib tomllib, Python 3.11+)."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_CONFIG_PATHS = [
    Path("~/.config/sysagent/config.toml").expanduser(),
    Path("/etc/sysagent/config.toml"),
]


@dataclass
class LLMConfig:
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    api_key_env: str = "OPENAI_API_KEY"
    temperature: float = 0.1
    max_tool_rounds: int = 8

    @property
    def api_key(self) -> str | None:
        return os.environ.get(self.api_key_env)


@dataclass
class PolicyConfig:
    # readonly — только чтение (безопасный режим по умолчанию)
    # ask      — изменения требуют подтверждения в терминале
    # auto     — изменения выполняются без спроса (только для доверенных стендов!)
    mode: str = "ask"
    allow_dangerous: bool = False
    audit_log: Path = field(
        default_factory=lambda: Path("~/.local/state/sysagent/audit.jsonl").expanduser()
    )
    command_timeout: int = 20
    max_output_bytes: int = 20_000


@dataclass
class Config:
    llm: LLMConfig = field(default_factory=LLMConfig)
    policy: PolicyConfig = field(default_factory=PolicyConfig)
    source: Path | None = None

    @classmethod
    def load(cls, path: str | Path | None = None) -> "Config":
        cfg = cls()
        candidate: Path | None = Path(path).expanduser() if path else None
        if candidate is None:
            for p in DEFAULT_CONFIG_PATHS:
                if p.is_file():
                    candidate = p
                    break
        if candidate and candidate.is_file():
            data = tomllib.loads(candidate.read_text(encoding="utf-8"))
            cfg.source = candidate
            llm = data.get("llm", {})
            for key, value in llm.items():
                if hasattr(cfg.llm, key):
                    setattr(cfg.llm, key, value)
            pol = data.get("policy", {})
            for key, value in pol.items():
                if key == "audit_log":
                    value = Path(value).expanduser()
                if hasattr(cfg.policy, key):
                    setattr(cfg.policy, key, value)
        # переменные окружения имеют приоритет над файлом
        if os.environ.get("SYSAGENT_MODEL"):
            cfg.llm.model = os.environ["SYSAGENT_MODEL"]
        if os.environ.get("SYSAGENT_BASE_URL"):
            cfg.llm.base_url = os.environ["SYSAGENT_BASE_URL"]
        if os.environ.get("SYSAGENT_MODE") in {"readonly", "ask", "auto"}:
            cfg.policy.mode = os.environ["SYSAGENT_MODE"]
        return cfg
