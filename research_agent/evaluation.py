"""Matched-question ReAct versus single-prompt CoT benchmark."""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import time

from langchain_core.messages import HumanMessage, SystemMessage

from .hotpotqa import DATASET_CONFIG, DATASET_ID, DATASET_SPLIT, fetch_hotpotqa_100
from .llm import response_text, token_usage
from .metrics import answer_em, answer_f1
from .react_agent import ReActResearchAgent


BASELINE_PROMPT = """You answer multi-hop factual questions without any external tools or retrieval.
Use only your internal knowledge. Provide a short, visible step-by-step explanation
then finish with a separate line exactly in the form:
FINAL_ANSWER: <short answer>
If uncertain, say so. Do not invent citations. Keep the final answer concise."""


def cot_baseline(model, question: str) -> dict:
    response = model.invoke([
        SystemMessage(content=BASELINE_PROMPT), HumanMessage(content=question),
    ])
    output = response_text(response)
    found = re.search(r"(?im)^\s*FINAL_ANSWER:\s*(.+?)\s*$", output)
    lines = output.strip().splitlines()
    answer = found.group(1).strip() if found else (lines[-1].strip() if lines else "I could not answer.")
    usage = token_usage(response)
    return {
        "answer": answer, "reasoning_excerpt": output[:1500],
        "tool_calls": 0, "input_tokens": usage["input_tokens"],
        "output_tokens": usage["output_tokens"],
        "total_tokens": usage["input_tokens"] + usage["output_tokens"],
        "status": "completed",
    }


def _read_jsonl(path: Path) -> dict[str, dict]:
    records = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                item = json.loads(line)
                records[str(item["id"])] = item
    return records


def _append_jsonl(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as dest:
        dest.write(json.dumps(value, ensure_ascii=False) + "\n")


def _aggregate(records: list[dict], n_requested: int) -> dict:
    # A recorded abstention or step limit is an evaluated answer worth zero
    # accuracy, NOT a missing question to discard from the denominator.
    good = [record for record in records
            if record.get("status") in ("completed", "unverified", "step_limit")]
    count = len(good)
    return {
        "requested": n_requested,
        "completed": count,
        "failed": len(records) - count,
        "abstained": sum(x["status"] in ("unverified", "step_limit") for x in good),
        "exact_match_accuracy_pct": round(100 * sum(x["em"] for x in good) / count, 2) if count else None,
        "token_f1_pct": round(100 * sum(x["f1"] for x in good) / count, 2) if count else None,
        "mean_tool_calls_per_query": round(sum(x["tool_calls"] for x in good) / count, 3) if count else None,
        "mean_total_tokens_per_query": round(sum(x["total_tokens"] for x in good) / count, 1) if count else None,
        "total_input_tokens": sum(x["input_tokens"] for x in good),
        "total_output_tokens": sum(x["output_tokens"] for x in good),
        "total_tokens": sum(x["total_tokens"] for x in good),
    }


def _export_summary(folder: Path, requested: int, model_name: str,
                    selected_ids: set[str]) -> dict:
    methods = {}
    for name in ("react", "cot"):
        rows = [row for item_id, row in _read_jsonl(folder / f"{name}_results.jsonl").items()
                if item_id in selected_ids]
        methods[name] = _aggregate(rows, requested)
    comparison = {
        "dataset": f"{DATASET_ID}/{DATASET_CONFIG}/{DATASET_SPLIT}",
        "sample_rule": "first 100 rows, fixed order, no gold contexts in model inputs",
        "requested_questions": requested,
        "model": model_name,
        "run_date_utc": datetime.now(timezone.utc).isoformat(),
        "status": "complete" if all(v["completed"] == requested for v in methods.values()) else "incomplete",
        "methods": methods,
        "measurement_note": "Token figures use model provider usage metadata; memory disabled in this single-turn benchmark.",
    }
    (folder / "summary.json").write_text(json.dumps(comparison, indent=2), encoding="utf-8")
    with (folder / "comparison.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["method", "completed", "exact_match_accuracy_pct", "token_f1_pct",
                         "mean_tool_calls_per_query", "mean_total_tokens_per_query",
                         "total_input_tokens", "total_output_tokens", "total_tokens"])
        for name, item in methods.items():
            writer.writerow([name] + [item[key] for key in (
                "completed", "exact_match_accuracy_pct", "token_f1_pct",
                "mean_tool_calls_per_query", "mean_total_tokens_per_query",
                "total_input_tokens", "total_output_tokens", "total_tokens")])
    return comparison


def evaluate(model, *, project_root: Path, limit: int = 100, max_steps: int = 6,
             output_dir: Path | None = None, pause: float = 0.0, refresh: bool = False) -> dict:
    if not 1 <= limit <= 100:
        raise ValueError("limit must be from 1 to 100")
    dataset = fetch_hotpotqa_100(project_root / "data" / "hotpotqa_100.json", refresh=refresh)[:limit]
    folder = output_dir or project_root / "output" / "evaluation"
    folder.mkdir(parents=True, exist_ok=True)
    agent = ReActResearchAgent(model, max_steps=max_steps)
    for method in ("react", "cot"):
        file = folder / f"{method}_results.jsonl"
        completed = _read_jsonl(file)
        for index, question in enumerate(dataset, 1):
            item_id = str(question["id"])
            if item_id in completed and completed[item_id].get("status") in (
                "completed", "unverified", "step_limit"
            ):
                continue
            print(f"[{method.upper()}] {index}/{limit}: {question['question'][:85]}", flush=True)
            started = time.monotonic()
            try:
                if method == "react":
                    result = agent.run(
                        question["question"], trace_path=folder / "traces" / f"{item_id}.jsonl",
                        run_id=item_id,
                    )
                else:
                    result = cot_baseline(model, question["question"])
                row = {
                    "id": item_id, "question": question["question"],
                    "gold_answer": question["answer"], "type": question["type"],
                    "difficulty": question["level"], "prediction": result["answer"],
                    "em": answer_em(result["answer"], question["answer"]),
                    "f1": answer_f1(result["answer"], question["answer"]),
                    "status": result["status"], "tool_calls": result["tool_calls"],
                    "input_tokens": result["input_tokens"],
                    "output_tokens": result["output_tokens"],
                    "total_tokens": result["total_tokens"],
                    "latency_seconds": round(time.monotonic() - started, 2),
                }
            except Exception as exc:
                row = {
                    "id": item_id, "question": question["question"],
                    "gold_answer": question["answer"], "status": "error",
                    "error": f"{type(exc).__name__}: {exc}",
                }
                print("  ERROR:", row["error"], flush=True)
            _append_jsonl(file, row)
            completed[item_id] = row
            if pause:
                time.sleep(pause)
    # Re-export from distinct IDs, including retried (latest) records.
    model_name = getattr(model, "model_name", getattr(model, "model", "custom"))
    return _export_summary(folder, limit, str(model_name),
                           {str(item["id"]) for item in dataset})

