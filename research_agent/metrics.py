"""Official-style HotpotQA answer normalization, exact match and token F1."""
from __future__ import annotations

from collections import Counter
import re
import string


def normalize_answer(text: str) -> str:
    text = text.lower()
    text = "".join(char for char in text if char not in string.punctuation)
    text = re.sub(r"\b(a|an|the)\b", " ", text)
    return " ".join(text.split())


def answer_em(prediction: str, gold: str) -> float:
    return float(normalize_answer(prediction) == normalize_answer(gold))


def answer_f1(prediction: str, gold: str) -> float:
    pred_tokens = normalize_answer(prediction).split()
    gold_tokens = normalize_answer(gold).split()
    special = {"yes", "no", "noanswer"}
    if pred_tokens and gold_tokens and (pred_tokens[0] in special or gold_tokens[0] in special):
        return float(pred_tokens == gold_tokens)
    common = Counter(pred_tokens) & Counter(gold_tokens)
    overlap = sum(common.values())
    if overlap == 0:
        return float(not pred_tokens and not gold_tokens)
    precision = overlap / len(pred_tokens)
    recall = overlap / len(gold_tokens)
    return 2 * precision * recall / (precision + recall)

