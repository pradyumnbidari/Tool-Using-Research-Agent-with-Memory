"""Single session turn orchestration and comparison of the memory variants."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import re
import uuid

from .memory import load_memory, save_memory
from .react_agent import ReActResearchAgent


def safe_session_id(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", value):
        raise ValueError("Session ID must be 1-48 letters, numbers, underscores or hyphens")
    return value


class ResearchSession:
    def __init__(self, model, root: Path, kind: str = "buffer", session_id: str = "demo",
                 max_steps: int = 6, persist: bool = True):
        self.root = root
        self.kind = kind
        self.session_id = safe_session_id(session_id)
        self.persist = persist
        self.memory_path = root / "output" / "sessions" / f"{self.session_id}.json" if persist else None
        self.memory = load_memory(kind, model, self.memory_path)
        self.agent = ReActResearchAgent(model, max_steps=max_steps)

    def ask(self, question: str) -> dict:
        context = self.memory.context(question)
        run_id = uuid.uuid4().hex[:12]
        trace = self.root / "output" / "traces" / self.session_id / f"{run_id}.jsonl"
        result = self.agent.run(question, context, trace_path=trace, run_id=run_id)
        before = self.memory.memory_tokens.copy()
        self.memory.record(question, result["answer"])
        result["memory_input_tokens"] = self.memory.memory_tokens["input_tokens"] - before["input_tokens"]
        result["memory_output_tokens"] = self.memory.memory_tokens["output_tokens"] - before["output_tokens"]
        result["memory_context_chars"] = len(context)
        result["memory_type"] = self.kind
        if self.persist:
            save_memory(self.memory, self.memory_path)
        return result


MEMORY_TEST_TURNS = [
    ("Please remember: my project code name is Orion.", None),
    ("Remember: the Orion project budget is 4500 rupees.", None),
    ("What is my project code name? Reply with the name only.", "Orion"),
    ("What is the budget for that project? Reply with the number only.", "4500"),
]


def compare_memories(model, project_root: Path, max_steps: int = 6) -> dict:
    output = project_root / "output" / "memory_comparison"
    output.mkdir(parents=True, exist_ok=True)
    samples = []
    metrics = {}
    for memory_type in ("buffer", "summary", "entity"):
        session = ResearchSession(model, project_root, memory_type,
                                  session_id=f"comparison_{memory_type}",
                                  max_steps=max_steps, persist=False)
        correct, graded = 0, 0
        agent_tokens, memory_tokens, context_chars = 0, 0, 0
        for turn, (question, expected) in enumerate(MEMORY_TEST_TURNS, 1):
            result = session.ask(question)
            answer = result["answer"]
            hit = expected.lower() in answer.lower() if expected else None
            if hit is not None:
                graded += 1
                correct += int(hit)
            agent_tokens += result["total_tokens"]
            memory_tokens += result["memory_input_tokens"] + result["memory_output_tokens"]
            context_chars += result["memory_context_chars"]
            samples.append({"memory": memory_type, "turn": turn, "question": question,
                            "answer": answer, "expected": expected, "hit": hit,
                            "memory_context_chars": result["memory_context_chars"],
                            "agent_tokens": result["total_tokens"],
                            "memory_update_tokens": result["memory_input_tokens"] + result["memory_output_tokens"],
                            "tool_calls": result["tool_calls"], "trace_file": result["trace_file"]})
        metrics[memory_type] = {
            "graded_followups": graded, "correct_followups": correct,
            "followup_accuracy_pct": round(100 * correct / graded, 1) if graded else None,
            "total_agent_tokens": agent_tokens, "total_memory_update_tokens": memory_tokens,
            "combined_tokens": agent_tokens + memory_tokens,
            "sum_memory_context_chars": context_chars,
            "final_memory_state": session.memory.snapshot(),
        }
    report = {"note": "Small illustrative 4-turn comparison; NOT HotpotQA accuracy.",
              "methods": metrics, "per_turn": samples}
    (output / "memory_comparison.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    with (output / "memory_comparison.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["memory", "graded_followups", "correct_followups", "followup_accuracy_pct",
                         "total_agent_tokens", "total_memory_update_tokens", "combined_tokens",
                         "sum_memory_context_chars"])
        for kind, summary in metrics.items():
            writer.writerow([kind] + [summary[k] for k in (
                "graded_followups", "correct_followups", "followup_accuracy_pct",
                "total_agent_tokens", "total_memory_update_tokens", "combined_tokens",
                "sum_memory_context_chars")])
    return report

