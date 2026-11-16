import json
import sys
from types import SimpleNamespace

import pytest

import research_agent.llm as llm


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class FakeOllamaModel:
    def __init__(self, **kwargs):
        self.options = kwargs


def test_free_local_provider(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.setenv("OLLAMA_MODEL", "qwen2.5:3b")
    monkeypatch.setattr(llm, "urlopen", lambda *_args, **_kwargs: FakeResponse())
    monkeypatch.setattr(llm.json, "load", lambda _stream: {"models": [{"name": "qwen2.5:3b"}]})
    monkeypatch.setitem(sys.modules, "langchain_ollama", SimpleNamespace(ChatOllama=FakeOllamaModel))
    model = llm.build_llm()
    assert model.options["model"] == "qwen2.5:3b"
    assert model.options["base_url"] == "http://localhost:11434"


def test_missing_model_has_helpful_message(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.setattr(llm, "urlopen", lambda *_args, **_kwargs: FakeResponse())
    monkeypatch.setattr(llm.json, "load", lambda _stream: {"models": []})
    with pytest.raises(RuntimeError, match="ollama pull"):
        llm.build_llm()
