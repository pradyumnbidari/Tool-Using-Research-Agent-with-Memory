"""Streamlit dashboard for the local Tool-Using Research Agent with Memory.

Run from the project root with: python -m streamlit run app.py
All benchmark values come from saved experiment files, never hard-coded scores.
"""
from __future__ import annotations

import csv
from io import StringIO
import json
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
from uuid import uuid4

import pandas as pd
import streamlit as st

from research_agent.llm import build_llm
from research_agent.session import ResearchSession, safe_session_id


ROOT = Path(__file__).resolve().parent
REPO_URL = "https://github.com/pradyumnbidari/Tool-Using-Research-Agent-with-Memory"
FINAL = ROOT / "output" / "final_100"
MEMORY = ROOT / "output" / "memory_comparison" / "memory_comparison.json"
SECTIONS = ["Research Chat", "Benchmark Results", "Memory Lab", "Trace Explorer", "About Project"]
ICONS = {"Research Chat": "💬", "Benchmark Results": "📊", "Memory Lab": "🧠", "Trace Explorer": "🔍", "About Project": "ℹ️"}


st.set_page_config(page_title="Research Agent | AI Lab", page_icon="🔎", layout="wide", initial_sidebar_state="expanded")


def use_theme() -> None:
    css_file = ROOT / "ui_theme.css"
    if css_file.is_file():
        st.markdown("<style>" + css_file.read_text(encoding="utf-8") + "</style>", unsafe_allow_html=True)


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def read_jsonl(path: Path) -> list[dict]:
    records = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                    if isinstance(row, dict):
                        records.append(row)
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return records


def fmt_number(value, decimals: int = 0) -> str:
    try:
        return f"{float(value):,.{decimals}f}"
    except (ValueError, TypeError):
        return "—"


def title(eyebrow: str, heading: str, description: str) -> None:
    st.markdown(f'<div class="eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
    st.title(heading)
    st.caption(description)


def empty_state(message: str, detail: str = "") -> None:
    st.info(message)
    if detail:
        st.caption(detail)


def ollama_status() -> tuple[bool, list[str]]:
    """Small, read-only health check; no dependency on Ollama to view reports."""
    try:
        with urlopen("http://localhost:11434/api/tags", timeout=1.5) as response:
            data = json.loads(response.read().decode("utf-8"))
        names = [item.get("name", "") for item in data.get("models", []) if isinstance(item, dict)]
        return True, names
    except (OSError, ValueError, HTTPError, URLError):
        return False, []


def trace_timeline(events: list[dict], key: str) -> None:
    if not events:
        st.caption("No steps were recorded for this request.")
        return
    for idx, event in enumerate(events, start=1):
        action = str(event.get("action", event.get("tool", "step")))
        with st.expander(f"Step {idx:02d}  ·  {action}", expanded=idx == 1):
            rationale = event.get("thought_summary") or event.get("thought") or event.get("message")
            if rationale:
                st.markdown("**Decision summary**")
                st.write(str(rationale))
            arguments = event.get("action_input") or event.get("input")
            if arguments not in (None, ""):
                st.markdown("**Tool input**")
                st.code(str(arguments), language="text")
            observation = event.get("observation") or event.get("result")
            if observation not in (None, ""):
                st.markdown("**Observation**")
                st.write(str(observation))
            if not any(k in event for k in ("thought_summary", "thought", "message", "observation", "result")):
                st.json(event)


def create_csv(rows: list[dict]) -> str:
    if not rows:
        return ""
    columns = list(dict.fromkeys(key for row in rows for key in row.keys()))
    stream = StringIO()
    writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


use_theme()

with st.sidebar:
    st.markdown('<div class="sidebar-brand"><span class="brand-icon">✦</span> RESEARCH <span>LAB</span></div>', unsafe_allow_html=True)
    st.caption("TOOL-USING AI · LOCAL & FREE")
    st.divider()
    active = st.radio("WORKSPACE", SECTIONS, format_func=lambda item: f"{ICONS[item]}  {item}", label_visibility="collapsed")
    st.divider()
    connected, models = ollama_status()
    if connected:
        st.success("● Ollama is online", icon="✅")
        model_name = next((name for name in models if name.startswith("qwen2.5:3b")), None)
        if model_name:
            st.caption(f"Loaded model: {model_name}")
        else:
            st.warning("Ollama is running; download qwen2.5:3b if missing.")
    else:
        st.warning("● Ollama is offline")
        st.caption("Launch Ollama to use live chat. Saved results still work.")
    st.markdown('<div class="sidebar-foot">PES UNIVERSITY · PROMPT ENGINEERING<br>QWEN2.5:3B + LANGGRAPH</div>', unsafe_allow_html=True)


if active == "Research Chat":
    title("01 / INTERACTIVE AGENT", "Your AI research workspace", "Ask multi-step questions. Watch the agent search Wikipedia, calculate, and remember context.")
    st.markdown('<div class="hero-strip"><span>✧</span> <strong>ReAct workflow</strong> &nbsp; Ask → Select tool → Observe → Answer <span class="hero-tag">100% local model</span></div>', unsafe_allow_html=True)

    with st.container(border=True):
        a, b, c = st.columns([1.2, 1.6, 1], gap="medium")
        with a:
            memory_type = st.selectbox("Memory strategy", ["buffer", "summary", "entity"], format_func=lambda x: x.title(), help="Buffer stores conversation turns; Summary compresses them; Entity keeps named facts.")
        with b:
            default_id = st.session_state.get("chat_id", "web_demo")
            session_id = st.text_input("Session ID", value=default_id, max_chars=48, help="Use letters, numbers, - or _. Separate names avoid mixing sessions.")
            st.session_state["chat_id"] = session_id
        with c:
            max_steps = st.slider("Max tool steps", min_value=1, max_value=10, value=6)
        if st.button("＋ Start fresh session", use_container_width=False):
            st.session_state["chat_id"] = f"web_{uuid4().hex[:8]}"
            st.rerun()

    session_ok = True
    try:
        safe_session_id(session_id)
    except ValueError as exc:
        st.error(str(exc))
        session_ok = False

    if not connected:
        st.warning("Live responses require Ollama running on your laptop. First launch Ollama, then return to this page.")

    history_key = f"ui_conversation_{session_id}_{memory_type}"
    history = st.session_state.setdefault(history_key, [])
    if not history:
        st.markdown("#### Try a question")
        presets = [
            "Who co-founded Microsoft, and in which year?",
            "How old was Bill Gates when Microsoft was founded?",
            "What is (1975 - 1955) - 1? Use the calculator tool.",
        ]
        cards = st.columns(3)
        for idx, suggestion in enumerate(presets):
            with cards[idx]:
                if st.button(suggestion, key=f"sample_{idx}", use_container_width=True, disabled=not connected or not session_ok):
                    st.session_state["prefilled_question"] = suggestion
                    st.rerun()

    for pos, item in enumerate(history):
        with st.chat_message("user"):
            st.write(item["question"])
        with st.chat_message("assistant"):
            st.write(item["answer"])
            st.caption(f"{item['tool_calls']} tool calls  ·  {fmt_number(item['total_tokens'])} tokens  ·  {item['memory_type'].title()} memory")
            with st.expander("View tool activity"):
                trace_timeline(item.get("trace", []), key=f"old_{pos}")
            if item.get("trace"):
                st.download_button("↓ Download trace", data="\n".join(json.dumps(event, ensure_ascii=False) for event in item["trace"]), file_name=f"trace_{pos + 1}.jsonl", mime="application/x-ndjson", key=f"download_{pos}")

    typed = st.chat_input("Ask your agent anything...", disabled=not connected or not session_ok)
    question = st.session_state.pop("prefilled_question", None) or typed
    if question and connected and session_ok:
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            with st.spinner("Researching with local Qwen + tools..."):
                try:
                    model = build_llm()
                    session = ResearchSession(model, ROOT, kind=memory_type, session_id=session_id, max_steps=max_steps)
                    result = session.ask(question)
                except Exception as exc:
                    st.error(f"Agent could not complete this turn: {type(exc).__name__}: {exc}")
                else:
                    answer = str(result.get("answer", "No answer returned."))
                    st.write(answer)
                    st.caption(f"{result.get('tool_calls', 0)} tool calls  ·  {fmt_number(result.get('total_tokens', 0))} tokens")
                    with st.expander("View tool activity"):
                        trace_timeline(result.get("trace", []), key="latest")
                    history.append({
                        "question": question, "answer": answer,
                        "trace": result.get("trace", []),
                        "tool_calls": result.get("tool_calls", 0),
                        "total_tokens": result.get("total_tokens", 0),
                        "memory_type": memory_type,
                    })

    st.caption("Tip: Existing saved memory continues when you reuse the same session ID. A fresh session starts with a new ID.")


elif active == "Benchmark Results":
    title("02 / EVIDENCE & EVALUATION", "100-question benchmark", "Real HotpotQA results generated by the project, comparing ReAct with a Chain-of-Thought baseline.")
    report = read_json(FINAL / "summary.json")
    methods = report.get("methods", {})
    react = methods.get("react", {})
    cot = methods.get("cot", {})
    if not (react and cot):
        empty_state("Benchmark summary not found.", "Copy the output/final_100/ folder from your actual evaluation into the project; do not substitute made-up results.")
    else:
        st.markdown('<div class="eyebrow">VERIFIED EXPERIMENT · 100 SAMPLES · FIXED ORDER</div>', unsafe_allow_html=True)
        cols = st.columns(4)
        cols[0].metric("ReAct Exact Match", f"{fmt_number(react.get('exact_match_accuracy_pct'), 1)}%")
        cols[1].metric("CoT Exact Match", f"{fmt_number(cot.get('exact_match_accuracy_pct'), 1)}%")
        cols[2].metric("Avg. ReAct Tools", fmt_number(react.get("mean_tool_calls_per_query"), 2))
        cols[3].metric("Questions per Method", str(react.get("completed", "—")))

        left, right = st.columns(2, gap="large")
        with left, st.container(border=True):
            st.subheader("Answer quality")
            quality = pd.DataFrame([
                {"Method": "ReAct", "Exact Match (%)": react.get("exact_match_accuracy_pct", 0), "Token F1 (%)": react.get("token_f1_pct", 0)},
                {"Method": "CoT", "Exact Match (%)": cot.get("exact_match_accuracy_pct", 0), "Token F1 (%)": cot.get("token_f1_pct", 0)},
            ]).set_index("Method")
            st.bar_chart(quality, horizontal=True, color=["#38D9CA", "#6279FF"], use_container_width=True)
        with right, st.container(border=True):
            st.subheader("Cost in model tokens")
            tokens = pd.DataFrame([
                {"Method": "ReAct", "Avg tokens / question": react.get("mean_total_tokens_per_query", 0)},
                {"Method": "CoT", "Avg tokens / question": cot.get("mean_total_tokens_per_query", 0)},
            ]).set_index("Method")
            st.bar_chart(tokens, horizontal=True, color="#6279FF", use_container_width=True)

        st.info("In this run, CoT scored higher than ReAct. ReAct made tool calls but often reached the step limit; this is a measured result, not a claim that tool use always improves accuracy.")
        st.caption(f"ReAct abstentions: {react.get('abstained', '—')} / {react.get('completed', '—')}.  CoT abstentions: {cot.get('abstained', '—')} / {cot.get('completed', '—')}.  {report.get('measurement_note', '')}")

        st.subheader("Explore individual answers")
        method_name = st.radio("Result set", ["ReAct", "CoT"], horizontal=True)
        selected_file = FINAL / ("react_results.jsonl" if method_name == "ReAct" else "cot_results.jsonl")
        rows = read_jsonl(selected_file)
        if rows:
            search = st.text_input("Search a question or answer", placeholder="e.g., nationality, Microsoft, 1975")
            show = [row for row in rows if search.casefold() in " ".join(str(row.get(k, "")) for k in ("question", "prediction", "gold_answer")).casefold()]
            view = [{
                "#": idx + 1,
                "Question": row.get("question", ""),
                "Expected": row.get("gold_answer", ""),
                "Predicted": row.get("prediction", ""),
                "EM": row.get("em", ""),
                "F1": row.get("f1", ""),
                "Tools": row.get("tool_calls", 0),
            } for idx, row in enumerate(show)]
            st.dataframe(view, use_container_width=True, hide_index=True, height=400)
            st.caption(f"Showing {len(show)} of {len(rows)} saved questions.")
            st.download_button("↓ Download filtered results as CSV", create_csv(view), file_name=f"{method_name.lower()}_results_view.csv", mime="text/csv")
        else:
            empty_state("Detailed result file not found for this method.")


elif active == "Memory Lab":
    title("03 / CONVERSATIONAL INTELLIGENCE", "Memory strategy comparison", "Three ways to remember previous turns: raw buffer, compressed summary, or extracted entities.")
    report = read_json(MEMORY)
    methods = report.get("methods", {})
    if not methods:
        empty_state("Memory comparison results not found.", "This page reads output/memory_comparison/memory_comparison.json.")
    else:
        descriptions = {
            "buffer": "Stores previous user and assistant messages as conversation history.",
            "summary": "Condenses older conversations into a shorter running summary.",
            "entity": "Keeps named entities and important facts as structured key-value memory.",
        }
        cards = st.columns(3, gap="medium")
        for idx, kind in enumerate(("buffer", "summary", "entity")):
            row = methods.get(kind, {})
            with cards[idx], st.container(border=True):
                st.markdown(f"### {kind.title()} memory")
                st.write(descriptions[kind])
                st.metric("Follow-up recall", f"{row.get('correct_followups', '—')} / {row.get('graded_followups', '—')}")
                st.caption(f"{fmt_number(row.get('followup_accuracy_pct'), 1)}% accuracy in the small recall trial")
                st.caption(f"Memory update: {fmt_number(row.get('total_memory_update_tokens'))} tokens")

        comparison = pd.DataFrame([
            {"Strategy": kind.title(), "Combined tokens": methods.get(kind, {}).get("combined_tokens", 0), "Recall accuracy (%)": methods.get(kind, {}).get("followup_accuracy_pct", 0)}
            for kind in ("buffer", "summary", "entity")
        ]).set_index("Strategy")
        left, right = st.columns(2, gap="large")
        with left, st.container(border=True):
            st.subheader("Total model tokens")
            st.bar_chart(comparison[["Combined tokens"]], horizontal=True, color="#38D9CA")
        with right, st.container(border=True):
            st.subheader("Follow-up recall")
            st.bar_chart(comparison[["Recall accuracy (%)"]], horizontal=True, color="#6279FF")

        st.warning("Important: this memory comparison grades only 2 follow-up recall questions per strategy. It is an illustrative 4-turn trial, NOT a 100-question HotpotQA accuracy score.")
        with st.expander("See the four-turn memory experiment"):
            display = [{"Memory": row.get("memory", ""), "Turn": row.get("turn", ""), "Question": row.get("question", ""), "Answer": row.get("answer", ""), "Expected": row.get("expected") or "—", "Correct": "—" if row.get("hit") is None else ("Yes" if row["hit"] else "No")} for row in report.get("per_turn", [])]
            st.dataframe(display, use_container_width=True, hide_index=True)
        with st.expander("Inspect final stored memory state"):
            kind = st.selectbox("Strategy", [k for k in ("buffer", "summary", "entity") if k in methods], key="memory_snapshot")
            st.json(methods[kind].get("final_memory_state", {}))


elif active == "Trace Explorer":
    title("04 / AGENT OBSERVABILITY", "Tool activity explorer", "Read the actual recorded steps and observations behind the model's answers.")
    location = st.radio("Trace source", ["100-question evaluation", "Live chat sessions"], horizontal=True)
    if location == "100-question evaluation":
        folder = FINAL / "traces"
        candidates = sorted(folder.glob("*.jsonl")) if folder.is_dir() else []
        evaluation = read_jsonl(FINAL / "react_results.jsonl")
        by_id = {str(row.get("id")): row for row in evaluation}
    else:
        folder = ROOT / "output" / "traces"
        candidates = sorted(folder.glob("*/*.jsonl")) if folder.is_dir() else []
        by_id = {}
    if not candidates:
        empty_state("No trace files found for this source.", "Evaluation traces belong in output/final_100/traces/. Live sessions write to output/traces/<session-id>/.")
    else:
        st.metric("Saved trace files", len(candidates))
        def display_trace(path: Path) -> str:
            parts = re.findall(r"[A-Fa-f0-9]{24,32}", path.name)
            match = by_id.get(parts[0], {}) if parts else {}
            question = str(match.get("question", ""))
            return (question[:85] + "…" if len(question) > 85 else question) + f"  ·  {path.name}" if question else str(path.relative_to(folder))
        chosen = st.selectbox("Select a saved trace", candidates, format_func=display_trace)
        content = read_jsonl(chosen)
        st.caption(f"File: {chosen.relative_to(ROOT)}  ·  {len(content)} recorded events")
        trace_timeline(content, key=f"file_{chosen.name}")
        st.download_button("↓ Download selected JSONL trace", chosen.read_bytes(), file_name=chosen.name, mime="application/x-ndjson")


else:
    title("05 / PROJECT OVERVIEW", "An agent that can research, reason & remember", "Prompt Engineering mini-project · PES University · Runs fully on your machine.")
    st.markdown("""
    This project uses a **local Qwen 2.5 (3B) model** through Ollama. A **LangGraph ReAct agent**
    decides when to search Wikipedia, calculate expressions, or run restricted Python, and records
    each tool step. Three memory approaches make multi-turn interaction possible.
    """)
    st.subheader("How it works")
    steps = st.columns(4, gap="small")
    for col, number, heading, detail in zip(steps, ("01", "02", "03", "04"), ("Ask", "Reason + Act", "Observe", "Remember"), ("Enter a question", "Choose a suitable tool", "Read the result and answer", "Save context for the next turn")):
        with col, st.container(border=True):
            st.caption(number)
            st.markdown(f"**{heading}**")
            st.write(detail)
    st.subheader("Research tools")
    st.markdown("- **Wikipedia search** — gathers public facts.\n- **Calculator** — evaluates safe numerical expressions.\n- **Restricted Python** — executes limited, controlled computations.\n- **Memory** — buffer, summary, and entity modes.")
    st.subheader("Project team")
    members = [
        ("Prathyush Gowda", "PES1UG24AM201"),
        ("Pradyumn Bidari", "PES1UG24AM194"),
        ("Prashant Devendra Naik", "PES1UG24AM199"),
        ("Pradyun Urs", "PES1UG24AM195"),
    ]
    st.dataframe(pd.DataFrame(members, columns=["Name", "SRN"]), use_container_width=True, hide_index=True)
    st.link_button("↗ Open project on GitHub", REPO_URL)
    docs = [("Project report", ROOT / "deliverables" / "Project_Report.pdf", "application/pdf"), ("Presentation", ROOT / "deliverables" / "Viva_Presentation_Team_Final.pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation")]
    for label, path, mime in docs:
        if path.exists():
            st.download_button("↓ " + label, data=path.read_bytes(), file_name=path.name, mime=mime)
    st.caption("No OpenAI API key, subscription, or paid credits are required.")
