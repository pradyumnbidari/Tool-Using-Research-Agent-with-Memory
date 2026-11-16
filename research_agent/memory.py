"""Three independent session-memory strategies and JSON session persistence."""
from __future__ import annotations

import json
from pathlib import Path
import re

from langchain_core.messages import HumanMessage, SystemMessage

from .llm import response_text, token_usage


def _usage_add(total: dict, usage: dict) -> None:
    total["input_tokens"] += usage["input_tokens"]
    total["output_tokens"] += usage["output_tokens"]


class SessionMemory:
    kind = "base"

    def __init__(self, model=None):
        self.model = model
        self.memory_tokens = {"input_tokens": 0, "output_tokens": 0}

    def context(self, query: str) -> str:
        raise NotImplementedError

    def record(self, question: str, answer: str) -> None:
        raise NotImplementedError

    def snapshot(self) -> dict:
        raise NotImplementedError

    def restore(self, payload: dict) -> None:
        raise NotImplementedError


class BufferMemory(SessionMemory):
    """Keeps all original Q/A turns verbatim."""
    kind = "buffer"

    def __init__(self, model=None):
        super().__init__(model)
        self.turns: list[dict[str, str]] = []

    def context(self, query: str) -> str:
        return "\n".join(
            f"User: {entry['question']}\nAssistant: {entry['answer']}" for entry in self.turns
        )

    def record(self, question: str, answer: str) -> None:
        self.turns.append({"question": question, "answer": answer})

    def snapshot(self) -> dict:
        return {"turns": self.turns}

    def restore(self, payload: dict) -> None:
        self.turns = list(payload.get("turns", []))


class SummaryMemory(SessionMemory):
    """LLM-refreshed rolling compact summary, omitting original transcripts."""
    kind = "summary"

    def __init__(self, model=None):
        super().__init__(model)
        self.summary = ""

    def context(self, query: str) -> str:
        return self.summary

    def record(self, question: str, answer: str) -> None:
        if self.model is None:
            raise RuntimeError("SummaryMemory requires a model")
        response = self.model.invoke([
            SystemMessage(content=(
                "Update the rolling conversation summary in <= 140 words. "
                "Preserve specific names, dates, quantities, references and stated user "
                "preferences. Do not invent details. Return summary text only."
            )),
            HumanMessage(content=(
                f"PREVIOUS SUMMARY:\n{self.summary or '(empty)'}\n\n"
                f"NEW USER MESSAGE:\n{question}\n\nNEW ASSISTANT ANSWER:\n{answer}"
            )),
        ])
        self.summary = response_text(response).strip()[:1800]
        _usage_add(self.memory_tokens, token_usage(response))

    def snapshot(self) -> dict:
        return {"summary": self.summary}

    def restore(self, payload: dict) -> None:
        self.summary = str(payload.get("summary", ""))


class EntityMemory(SessionMemory):
    """LLM-extracted entity -> short fact maps updated after every turn."""
    kind = "entity"

    def __init__(self, model=None):
        super().__init__(model)
        self.entities: dict[str, str] = {}

    def context(self, query: str) -> str:
        if not self.entities:
            return ""
        matches = [
            (name, facts) for name, facts in self.entities.items()
            if re.search(r"\b" + re.escape(name) + r"\b", query, flags=re.I)
        ]
        selected = matches or list(self.entities.items())[-8:]
        return "\n".join(f"{name}: {facts}" for name, facts in selected)[:2500]

    def record(self, question: str, answer: str) -> None:
        if self.model is None:
            raise RuntimeError("EntityMemory requires a model")
        extractor = self.model.bind(format="json") if type(self.model).__name__ == "ChatOllama" else self.model
        response = extractor.invoke([
            SystemMessage(content=(
                "Extract or update explicitly stated named people, projects, places, "
                "organizations and their concrete facts. Return ONLY a JSON object "
                "mapping each entity name to a concise factual string. Include "
                "existing entries that remain true. Merge updates; do not invent entities. "
                "At most 25 entities, at most 180 characters per value."
            )),
            HumanMessage(content=(
                f"EXISTING ENTITY MAP:\n{json.dumps(self.entities)}\n\n"
                f"USER MESSAGE:\n{question}\nASSISTANT ANSWER:\n{answer}"
            )),
        ])
        text = response_text(response).strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text).strip()
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                for name, facts in list(parsed.items())[:25]:
                    if isinstance(name, str) and isinstance(facts, str) and name.strip():
                        self.entities[name[:80]] = facts[:180]
        except json.JSONDecodeError:
            pass  # preserve existing entities rather than corrupt them
        self.entities = dict(list(self.entities.items())[-25:])
        _usage_add(self.memory_tokens, token_usage(response))

    def snapshot(self) -> dict:
        return {"entities": self.entities}

    def restore(self, payload: dict) -> None:
        self.entities = dict(payload.get("entities", {}))


MEMORY_TYPES = {"buffer": BufferMemory, "summary": SummaryMemory, "entity": EntityMemory}


def load_memory(kind: str, model, path: Path | None = None) -> SessionMemory:
    memory = MEMORY_TYPES[kind](model)
    if path and path.exists():
        saved = json.loads(path.read_text(encoding="utf-8"))
        if saved.get("kind") != kind:
            raise ValueError("Session exists with a different memory type. Choose a new session ID.")
        memory.restore(saved.get("state", {}))
    return memory


def save_memory(memory: SessionMemory, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps({"kind": memory.kind, "state": memory.snapshot()}, indent=2),
        encoding="utf-8",
    )
    temporary.replace(path)

