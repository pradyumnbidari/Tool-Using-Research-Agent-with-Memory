"""Free local Ollama model and token usage normalization."""
from __future__ import annotations

import os
import json
from urllib.request import urlopen
from urllib.error import URLError

from dotenv import load_dotenv


def build_llm():
    load_dotenv()
    provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
    if provider != "ollama":
        raise RuntimeError(
            "This free project uses Ollama. Set LLM_PROVIDER=ollama in .env. "
            "An OpenAI API key is not needed."
        )
    model_name = os.getenv("OLLAMA_MODEL", "qwen2.5:3b").strip()
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    if not base_url.startswith(("http://127.0.0.1:", "http://localhost:")):
        raise RuntimeError("For safety, OLLAMA_BASE_URL must point to localhost.")
    try:
        with urlopen(base_url + "/api/tags", timeout=3) as response:
            tags = json.load(response)
    except (OSError, URLError, ValueError) as exc:
        raise RuntimeError(
            "Ollama is not running on your PC. Start Ollama from the Windows Start "
            "menu. Then run `ollama list` in CMD and try again."
        ) from exc
    names = {item.get("name", item.get("model", "")) for item in tags.get("models", [])}
    if model_name not in names:
        raise RuntimeError(
            f"Local model {model_name!r} was not found. Run this in CMD first: "
            f"ollama pull {model_name}"
        )
    from langchain_ollama import ChatOllama

    return ChatOllama(model=model_name, base_url=base_url,
                      temperature=0, num_ctx=4096, num_predict=420)


def token_usage(response) -> dict[str, int]:
    """Prefer actual provider usage; never represent estimates as measured tokens."""
    usage = getattr(response, "usage_metadata", None) or {}
    metadata = getattr(response, "response_metadata", None) or {}
    fallback = metadata.get("token_usage") or {}
    return {
        "input_tokens": int(usage.get("input_tokens", fallback.get("prompt_tokens", metadata.get("prompt_eval_count", 0))) or 0),
        "output_tokens": int(usage.get("output_tokens", fallback.get("completion_tokens", metadata.get("eval_count", 0))) or 0),
    }


def response_text(response) -> str:
    value = response.content
    if isinstance(value, str):
        return value
    return "\n".join(
        part.get("text", "") for part in value if isinstance(part, dict) and part.get("type") == "text"
    )

