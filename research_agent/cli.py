"""Cross-platform command line entry point: python -m research_agent.cli ..."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .hotpotqa import fetch_hotpotqa_100
from .llm import build_llm
from .session import ResearchSession, compare_memories
from .evaluation import evaluate


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="ReAct tool-using research agent with memory")
    subs = parser.add_subparsers(dest="command", required=True)
    chat = subs.add_parser("chat", help="Ask a question or start interactive chat")
    chat.add_argument("--memory", choices=("buffer", "summary", "entity"), default="buffer")
    chat.add_argument("--session", default="demo", help="Stable session name, e.g. orion_buffer")
    chat.add_argument("--question", help="Ask once and exit (omit for interactive mode)")
    chat.add_argument("--max-steps", type=int, default=int(os.getenv("MAX_AGENT_STEPS", 6)))
    dataset = subs.add_parser("download-data", help="Download the exact 100 HotpotQA validation rows")
    dataset.add_argument("--refresh", action="store_true")
    subs.add_parser("check-model", help="Check the free local Ollama model with one short prompt")
    subs.add_parser("check-wikipedia", help="Check that live Wikipedia searches work")
    experiment = subs.add_parser("evaluate", help="Compare ReAct and CoT on matched HotpotQA questions")
    experiment.add_argument("--limit", type=int, default=100)
    experiment.add_argument("--max-steps", type=int, default=int(os.getenv("MAX_AGENT_STEPS", 6)))
    experiment.add_argument("--pause", type=float, default=0)
    experiment.add_argument("--output", type=Path, default=None)
    experiment.add_argument("--refresh", action="store_true")
    memory = subs.add_parser("compare-memory", help="Run identical four-turn dialogs with 3 memory modes")
    memory.add_argument("--max-steps", type=int, default=6)
    args = parser.parse_args()

    if args.command == "download-data":
        rows = fetch_hotpotqa_100(PROJECT_ROOT / "data" / "hotpotqa_100.json", args.refresh)
        print(f"Downloaded {len(rows)} official validation questions to data/hotpotqa_100.json")
        return


    if args.command == "check-wikipedia":
        from .tools import wikipedia_search
        print(wikipedia_search("Bill Gates")[:3000])
        return

    model = build_llm()
    if args.command == "check-model":
        from langchain_core.messages import HumanMessage
        response = model.invoke([HumanMessage(content="Reply with exactly the word OK.")])
        print("Local model:", model.model)
        print("Response:", response.content)
        print("No paid API key was used.")
    elif args.command == "chat":
        session = ResearchSession(model, PROJECT_ROOT, args.memory, args.session, args.max_steps)
        print(f"Session: {args.session} | Memory: {args.memory} | exit with /exit")
        while True:
            question = args.question or input("\nYou: ").strip()
            if question.lower() in ("/exit", "quit", "exit"):
                break
            if question:
                result = session.ask(question)
                print("\nAgent:", result["answer"])
                print(f"Tools: {result['tool_calls']} | Agent tokens: {result['total_tokens']} | "
                      f"Memory update tokens: {result['memory_input_tokens'] + result['memory_output_tokens']}")
                print("Trace:", result["trace_file"])
                for step in result["trace"]:
                    print("  Thought:", step.get("thought_summary", ""))
                    print("  Action:", step["action"], step.get("action_input", ""))
                    print("  Observation:", step.get("observation", "")[:250])
            if args.question:
                break
    elif args.command == "evaluate":
        result = evaluate(model, project_root=PROJECT_ROOT, limit=args.limit,
                          max_steps=args.max_steps, output_dir=args.output,
                          pause=args.pause, refresh=args.refresh)
        print(json.dumps(result, indent=2))
    elif args.command == "compare-memory":
        result = compare_memories(model, PROJECT_ROOT, max_steps=args.max_steps)
        print(json.dumps(result["methods"], indent=2))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, KeyboardInterrupt) as exc:
        raise SystemExit(str(exc)) from exc

