"""Optional Streamlit demonstration UI. Launch with: streamlit run app.py"""
from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from research_agent.llm import build_llm
from research_agent.session import ResearchSession


ROOT = Path(__file__).parent
st.set_page_config(page_title="ReAct Research Agent", page_icon="🔎", layout="wide")
st.title("🔎 Tool-Using Research Agent")
st.caption("ReAct with Wikipedia, calculator, restricted Python and conversation memory")

with st.sidebar:
    memory_type = st.selectbox("Memory strategy", ["buffer", "summary", "entity"])
    session_id = st.text_input("Session name", value=f"web_{memory_type}")
    steps = st.slider("Maximum tool calls", min_value=1, max_value=10, value=6)
    st.info("The trace shows short public decision summaries, tool actions and observations.")

try:
    llm = build_llm()
    current = ResearchSession(llm, ROOT, kind=memory_type, session_id=session_id, max_steps=steps)
except (RuntimeError, ValueError) as exc:
    st.error(str(exc))
    st.stop()

conversation_key = f"history_{session_id}_{memory_type}"
if conversation_key not in st.session_state:
    st.session_state[conversation_key] = []

for item in st.session_state[conversation_key]:
    with st.chat_message("user"):
        st.write(item["question"])
    with st.chat_message("assistant"):
        st.write(item["answer"])
        with st.expander("Thought / Action / Observation trace"):
            st.json(item["trace"])

question = st.chat_input("Ask a multi-hop fact or numerical question...")
if question:
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"):
        with st.spinner("Researching..."):
            try:
                answer = current.ask(question)
            except Exception as exc:
                st.error(f"Query failed: {type(exc).__name__}: {exc}")
                st.stop()
        st.write(answer["answer"])
        st.caption(f"Tools: {answer['tool_calls']} | Tokens: {answer['total_tokens']} | "
                   f"Memory update tokens: {answer['memory_input_tokens'] + answer['memory_output_tokens']}")
        with st.expander("Thought / Action / Observation trace"):
            st.json(answer["trace"])
    st.session_state[conversation_key].append({
        "question": question, "answer": answer["answer"], "trace": answer["trace"],
    })

