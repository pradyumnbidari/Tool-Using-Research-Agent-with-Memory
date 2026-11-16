"""Retrieve a fixed, deterministic HotpotQA distractor validation subset."""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DATASET_ID = "hotpotqa/hotpot_qa"
DATASET_CONFIG = "distractor"
DATASET_SPLIT = "validation"
SOURCE_URL = "https://datasets-server.huggingface.co/rows"


def fetch_hotpotqa_100(path: Path, refresh: bool = False) -> list[dict]:
    """Cache first 100 canonical validation examples (no gold context in prompts)."""
    if path.exists() and not refresh:
        data = json.loads(path.read_text(encoding="utf-8"))
        if len(data) != 100:
            raise ValueError("Cached dataset must contain exactly 100 questions")
        return data

    query = urlencode({
        "dataset": DATASET_ID, "config": DATASET_CONFIG,
        "split": DATASET_SPLIT, "offset": 0, "length": 100,
    })
    req = Request(SOURCE_URL + "?" + query, headers={"User-Agent": "MiniProjectHotpotQA/1.0"})
    try:
        with urlopen(req, timeout=60) as response:
            payload = json.load(response)
    except Exception as exc:
        raise RuntimeError(
            "Cannot download HotpotQA questions from Hugging Face. Check your internet "
            "connection and retry, or use a previously downloaded data/hotpotqa_100.json."
        ) from exc
    rows = payload.get("rows", [])
    if len(rows) != 100:
        raise RuntimeError(f"Expected exactly 100 HotpotQA rows, received {len(rows)}")
    result = []
    for item in rows:
        row = item["row"]
        result.append({
            "id": row.get("id", item.get("row_idx")),
            "question": row["question"], "answer": row["answer"],
            "type": row.get("type", ""), "level": row.get("level", ""),
        })
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result

