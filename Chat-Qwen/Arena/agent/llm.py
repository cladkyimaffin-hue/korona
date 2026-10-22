"""LLM-часть: цикл «модель -> инструмент -> наблюдение -> модель».

Используется любой OpenAI-совместимый эндпоинт (OpenAI, OpenRouter, Ollama,
vLLM, LM Studio), поэтому SDK не нужен — только stdlib urllib.

Замечание по безопасности: модель НЕ решает, можно ли выполнить команду.
Она лишь предлагает инструмент; решение принимает policy.py, а подтверждение
запрашивается у человека.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Callable

from .config import Config
from .tools import TOOLS, call_tool, openai_tool_schemas

SYSTEM_PROMPT = """Ты — системный администратор Linux-хоста. Ты работаешь через инструменты,
которые дают доступ к журналу systemd, статусу служб и метрикам.

Правила:
1. Сначала диагностика, потом действие. Никогда не меняй систему, пока не понял причину.
2. Используй journal_errors с группировкой — не проси 1000 строк лога.
3. Перед изменением (restart/stop/install) кратко объясни: что делаешь, зачем, и какой риск.
4. Если инструмент вернул отказ политики — не пытайся обойти его другими командами.
   Сообщи пользователю, что нужно разрешить в policy.py.
5. Отвечай по-русски, кратко и структурно. Команды, которые предлагаешь выполнить
   вручную, оформляй в ```bash блоке.
6. Если данных не хватает — задай один точный вопрос, а не десять.
"""


class LLMError(RuntimeError):
    pass


def chat_completion(cfg: Config, messages: list[dict], tools: list[dict] | None = None,
                    timeout: int = 120) -> dict[str, Any]:
    api_key = cfg.llm.api_key
    if not api_key:
        raise LLMError(
            f"не задан ключ: export {cfg.llm.api_key_env}=... "
            "(для Ollama/LM Studio поставьте любое значение, напр. 'ollama')"
        )
    payload: dict[str, Any] = {
        "model": cfg.llm.model,
        "messages": messages,
        "temperature": cfg.llm.temperature,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    url = cfg.llm.base_url.rstrip("/") + "/chat/completions"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:800]
        raise LLMError(f"HTTP {exc.code} от LLM: {detail}") from exc
    except urllib.error.URLError as exc:
        raise LLMError(f"не удалось соединиться с LLM ({url}): {exc.reason}") from exc


def run_agent_turn(cfg: Config, history: list[dict], user_message: str,
                   approve: Callable[[str, str], bool] | None = None,
                   verbose: bool = True) -> str:
    """Один ход диалога. history мутируется (дополняется) — для многоходового чата."""
    if not history:
        history.append({"role": "system", "content": SYSTEM_PROMPT})
    history.append({"role": "user", "content": user_message})

    schemas = openai_tool_schemas()
    for round_no in range(1, cfg.llm.max_tool_rounds + 1):
        data = chat_completion(cfg, history, tools=schemas)
        try:
            message = data["choices"][0]["message"]
        except (KeyError, IndexError) as exc:
            raise LLMError(f"неожиданный ответ LLM: {str(data)[:400]}") from exc

        tool_calls = message.get("tool_calls") or []
        if not tool_calls:
            answer = message.get("content") or ""
            history.append({"role": "assistant", "content": answer})
            return answer

        history.append({"role": "assistant", "content": message.get("content") or "",
                        "tool_calls": tool_calls})

        for call in tool_calls:
            fn = call["function"]["name"]
            try:
                args = json.loads(call["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            if verbose:
                print(f"  [tool {round_no}] {fn}({json.dumps(args, ensure_ascii=False)})")
            result = call_tool(fn, args, cfg, approve=approve)
            if verbose:
                preview = json.dumps(result, ensure_ascii=False)
                print(f"  [result] {preview[:300]}{'...' if len(preview) > 300 else ''}")
            history.append({"role": "tool", "tool_call_id": call.get("id", fn),
                            "name": fn,
                            "content": json.dumps(result, ensure_ascii=False)[:12_000]})

    return "Достигнут лимит раундов вызова инструментов — останавливаюсь. " \
           "Сузьте задачу или увеличьте llm.max_tool_rounds."


def describe_tools() -> str:
    lines = []
    for name, spec in TOOLS.items():
        params = ", ".join(spec["parameters"].get("properties", {}))
        flag = " [изменяет систему]" if spec.get("requires_approval") else ""
        lines.append(f"  {name}({params}){flag}\n      {spec['description'].splitlines()[0]}")
    return "\n".join(lines)
