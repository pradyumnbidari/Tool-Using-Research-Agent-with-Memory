"""Independent, named tools selected by the research agent."""
from __future__ import annotations

import ast
import math
import os
from pathlib import Path
import subprocess
import sys
import re
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json


_OPERATORS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.FloorDiv: lambda a, b: a // b,
    ast.Mod: lambda a, b: a % b,
    ast.Pow: lambda a, b: a**b,
}
_FUNCTIONS = {"sqrt": math.sqrt, "log": math.log, "abs": abs, "round": round}


def _arithmetic(node):
    if isinstance(node, ast.Expression):
        return _arithmetic(node.body)
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        if abs(node.value) > 1e12:
            raise ValueError("Numeric literal too large")
        return node.value
    if isinstance(node, ast.Name) and node.id in ("pi", "e"):
        return getattr(math, node.id)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        result = _arithmetic(node.operand)
        return +result if isinstance(node.op, ast.UAdd) else -result
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        left, right = _arithmetic(node.left), _arithmetic(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 100:
            raise ValueError("Exponent exceeds safe limit")
        result = _OPERATORS[type(node.op)](left, right)
        if isinstance(result, complex) or abs(result) > 1e100:
            raise ValueError("Result exceeds safe limit")
        return result
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.func.id in _FUNCTIONS and not node.keywords and len(node.args) <= 2:
            return _FUNCTIONS[node.func.id](*[_arithmetic(v) for v in node.args])
    raise ValueError("Calculator accepts only arithmetic, sqrt, log, abs, round, pi, e")


def calculator(expression: str) -> str:
    """Evaluate small arithmetic expressions without using eval()."""
    if len(expression) > 250:
        return "ERROR: expression too long"
    try:
        answer = _arithmetic(ast.parse(expression, mode="eval"))
        return str(answer)
    except (ValueError, TypeError, ZeroDivisionError, SyntaxError, OverflowError) as exc:
        return f"ERROR: {exc}"


def _wiki_json(params: dict) -> dict:
    query = urlencode({**params, "format": "json", "utf8": "1"})
    req = Request(
        "https://en.wikipedia.org/w/api.php?" + query,
        headers={"User-Agent": "StudentResearchAgent/1.0 (educational research; Python urllib)"},
    )
    for attempt in range(2):
        try:
            with urlopen(req, timeout=12) as response:
                return json.load(response)
        except OSError:
            if attempt == 1:
                raise
            time.sleep(0.5)


def wikipedia_search(query: str) -> str:
    """Search live Wikipedia and return excerpts with article URLs."""
    if not query.strip():
        return "ERROR: empty search query"
    try:
        found = _wiki_json({"action": "query", "list": "search", "srsearch": query[:250], "srlimit": 5})
        hits = found.get("query", {}).get("search", [])
        if not hits:
            return "No Wikipedia results found. Try a broader or different query."
        # Prefer direct topical articles over loosely related Wikipedia hits,
        # e.g. Microsoft over Outlook.com for a Microsoft-founder search.
        words = {word.lower() for word in re.findall(r"[A-Za-z]{3,}", query)}
        def relevance(hit):
            title = hit.get("title", "").lower()
            snippet = re.sub(r"<[^>]+>", " ", hit.get("snippet", "")).lower()
            return 3 * sum(word in title for word in words) + sum(word in snippet for word in words)
        hits = sorted(hits, key=relevance, reverse=True)[:3]
        titles = [hit["title"] for hit in hits]
        details = _wiki_json(
            {"action": "query", "prop": "extracts", "titles": "|".join(titles),
             "explaintext": 1, "exintro": 1, "exchars": 1500, "redirects": 1}
        )
        pages = details.get("query", {}).get("pages", {})
        by_title = {page.get("title"): page for page in pages.values()}
        lines = []
        for hit in hits:
            title = hit["title"]
            page = by_title.get(title, {})
            url = "https://en.wikipedia.org/wiki/" + title.replace(" ", "_")
            excerpt = page.get("extract", "")[:1500] or "No extract available."
            lines.append(f"TITLE: {title}\nURL: {url}\nEXCERPT: {excerpt}")
        return "\n\n".join(lines)[:5200]
    except Exception as exc:
        return f"ERROR: Wikipedia request failed ({type(exc).__name__}: {exc}). Try again."


def python_execute(code: str) -> str:
    """Run a restricted numerical Python subset in a time-limited child process."""
    if len(code) > 1200:
        return "ERROR: Python code exceeds 1200 characters"
    runner = Path(__file__).with_name("python_runner.py")
    env = {"PYTHONIOENCODING": "utf-8"}
    if os.name == "nt":
        env["SystemRoot"] = os.environ.get("SystemRoot", "C:\\Windows")
    try:
        proc = subprocess.run(
            [sys.executable, "-I", "-S", str(runner)], input=code, text=True,
            capture_output=True, timeout=4, env=env, check=False,
        )
        result = (proc.stdout.strip() or proc.stderr.strip() or "No printed output").strip()
        return ("ERROR: " if proc.returncode else "") + result[:2000]
    except subprocess.TimeoutExpired:
        return "ERROR: Python execution exceeded four seconds"


TOOLS = {
    "wikipedia_search": wikipedia_search,
    "calculator": calculator,
    "python_execute": python_execute,
}

TOOL_DESCRIPTIONS = """wikipedia_search: Search Wikipedia for factual information. Input is a search phrase.
calculator: Compute exact arithmetic. Input is one expression, e.g., (1879-1865)*12.
python_execute: Run a restricted Python numerical script. Input code can use lists,
variables, arithmetic, sum, len, min, max, range, round and print. Include print()."""

