"""Child-process-only, restricted subset of Python for numeric tasks.

Educational sandbox, not a security boundary for hostile third-party code.
"""
from __future__ import annotations

import ast
import sys

try:
    import resource

    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))
except (ImportError, ValueError, OSError):
    pass

ALLOWED_TYPES = (
    ast.Module, ast.Expr, ast.Assign, ast.Name, ast.Load, ast.Store,
    ast.Constant, ast.List, ast.Tuple, ast.Dict, ast.Set, ast.Subscript,
    ast.Slice, ast.BinOp, ast.UnaryOp, ast.Add, ast.Sub, ast.Mult, ast.Div,
    ast.FloorDiv, ast.Mod, ast.Pow, ast.UAdd, ast.USub, ast.Call,
    ast.ListComp, ast.comprehension, ast.Compare, ast.Eq, ast.NotEq,
    ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.IfExp, ast.BoolOp, ast.And, ast.Or,
)


def bounded_range(*args):
    result = range(*args)
    if len(result) > 10000:
        raise ValueError("range length exceeds 10,000")
    return result


SAFE = {
    "print": print, "sum": sum, "min": min, "max": max,
    "len": len, "abs": abs, "round": round, "range": bounded_range,
    "sorted": sorted, "int": int, "float": float, "enumerate": enumerate,
}


def main() -> None:
    code = sys.stdin.read(1201)
    if len(code) > 1200:
        raise ValueError("Code is too long")
    tree = ast.parse(code, mode="exec")
    if len(tree.body) > 16:
        raise ValueError("Too many statements")
    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED_TYPES):
            raise ValueError(f"Prohibited Python syntax: {type(node).__name__}")
        if isinstance(node, ast.Name) and (node.id.startswith("_") or "__" in node.id):
            raise ValueError("Private names are prohibited")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in SAFE:
                raise ValueError("Only approved numeric functions may be called")
        if isinstance(node, ast.Pow) and len(code) > 1000:
            raise ValueError("Exponentiation code is too long")
    scope = {"__builtins__": {}, **SAFE}
    exec(compile(tree, "<restricted_python>", "exec"), scope, scope)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)

