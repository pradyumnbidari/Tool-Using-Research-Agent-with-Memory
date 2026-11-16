# Viva guide - Tool-Using Research Agent with Memory

## 30-second introduction (say this to the panel)

"Our project is a Tool-Using Research Agent with Memory, implemented using LangGraph. When a user asks a complex question, our agent can break it into steps, look up facts through Wikipedia, perform precise arithmetic with a calculator, or run restricted Python for numerical problems. Every step records a short reasoning summary, the selected action and its observation. We also implemented three memory strategies and a fair benchmark on 100 HotpotQA questions against a single-prompt Chain-of-Thought baseline."

## What exactly is the problem statement?

"Ordinary single-prompt language models may answer multi-hop questions without verifying facts, make numerical mistakes and forget information across turns. Our system lets the model actively choose tools, use observations before answering, and retain session context."

## What is ReAct?

ReAct means **Reasoning and Acting**. The cycle is:

1. **Thought (public summary):** decide what fact or calculation is needed next.
2. **Action:** choose one tool and supply an input.
3. **Observation:** receive the actual result from that tool.
4. Repeat until enough evidence exists, then give a **final answer**.

The trace logs public decision summaries, not the model's inaccessible private thoughts.

## What is LangGraph doing?

It defines a small state machine with a **think node**, an **act node**, a conditional edge for **final answer**, and a loop back to think after a tool response. The state holds the current question, intermediate tool observations, token counts, trace and answer.

## Explain the three tools

| Tool | What it does | Simple example |
| --- | --- | --- |
| Wikipedia | Finds factual information from online articles | Search when Microsoft was founded |
| Calculator | Safely evaluates an arithmetic expression | `1975-1955` |
| Python execution | Handles a small numerical script | `print(sum([10,20,30])/3)` |

The Python tool accepts a restricted subset of Python and runs it in a separate timed process. We explicitly do not claim it is a production-grade code sandbox.

## Explain the three memory types

- **Buffer memory:** keeps entire earlier question-answer pairs. Preserves details but grows every turn.
- **Summary memory:** updates one compact summary after each turn. Saves prompt space in long sessions, but summarization can lose details and costs additional model tokens.
- **Entity memory:** stores named entities and their properties, e.g., `Orion: project budget 4500 rupees`. Efficient for fact recall, but may miss information that is not a named entity.

**Our measured four-turn memory test:** Buffer remembered both tested facts
(2/2, **100%**), summary also remembered both (2/2, **100%**), and entity
remembered one (1/2, **50%**). Combined token use was **11,147** for buffer,
**10,919** for summary, and **28,023** for entity. This is just two graded
recall prompts per method, so do not overclaim that one strategy always wins.

## What is multi-hop reasoning?

It means one question depends on several linked facts. Example: "How old was Microsoft's co-founder Bill Gates when Microsoft was founded?" Needs the birth year, the foundation year and subtraction. If exact dates are needed, the answer depends on the month/day, not only year subtraction.

## What is HotpotQA?

A Wikipedia-based multi-hop QA benchmark. We take the same first 100 questions from the **distractor validation split** and compare ReAct against CoT. Only the question text goes to either method. Gold answers are hidden from the model and used for scoring.

## What is the CoT baseline?

A single prompt that asks the LLM to briefly reason step-by-step and give `FINAL_ANSWER:`. It does **not** have a search, calculator, Python tool or memory. This tests whether tools improve the answers compared with a one-call baseline.

## How do we calculate accuracy?

**Exact Match % = (number of normalized answers exactly matching gold answers / 100 evaluated questions) x 100.**

The denominator includes incorrect answers and abstentions. A model saying it
cannot verify an answer does not receive credit for that question.

We also calculate token F1, mean tool calls and provider-reported input/output token usage. When a run is incomplete, we show how many of the 100 finished and do not present partial accuracy as a full-benchmark result.

## What's the novelty?

"Our independent contribution is combining an auditable, explicit LangGraph ReAct loop with three interchangeable memory systems, a restricted numerical Python tool, persistent session state, and a reproducible 100-question benchmark. We also measure the extra token cost of memory maintenance. These are implementation contributions, not a claim that ReAct or HotpotQA were invented by us."

## Actual 100-question results (say this to the panel)

"We evaluated the same 100 HotpotQA questions using the free Qwen2.5 3B model.
The tool-using ReAct agent achieved **7% exact-match accuracy**. The single-prompt
CoT baseline achieved **15%**. ReAct called tools **3.91 times per question** on
average and used about **7,372 tokens per query**, compared with about **167**
for CoT. Both methods completed all 100 questions with zero execution failures,
but ReAct abstained on **82** because it could not reliably verify or complete
the answer."

**If the teacher asks, 'Why did CoT beat your agent?'**

"Adding tools does not automatically improve answers. Our 3-billion-parameter
local model sometimes struggled to choose the next tool action and finish its
multi-step reasoning. Our safeguards also make it abstain instead of inventing
unsupported answers. These results are specific to our model and this evaluation;
a stronger model or better retrieval could change the comparison."

**If the teacher asks about memory results:**

"In our small four-turn test, buffer and summary both recalled 2 out of 2 facts;
entity recalled 1 out of 2. Summary used slightly fewer total tokens than buffer,
but it needed extra model calls to maintain the summary. The test sample is too
small to claim a general winner."

## Three questions the teacher may ask

**Q1. Why not directly ask ChatGPT?**
"The agent checks external facts and performs actual calculations, while providing inspectable steps and retaining conversation context."

**Q2. Does summary memory always beat buffer?**
"No. Buffer is complete but expensive in long sessions. Summary is shorter but may discard details. We compare them experimentally rather than assuming one wins."

**Q3. Can the agent run any code?**
"No. The Python tool is intentionally restricted to small numerical expressions, lists and approved functions. This reduces accidental damage but is not equivalent to a hardened remote sandbox."

## Free local model for the demo

"We run the Qwen2.5 3B model on our own laptop using Ollama, so no paid OpenAI API is required. The LangGraph framework and all three tools remain unchanged. The model may be slower than a hosted service because it runs on local hardware."

Run `ollama pull qwen2.5:3b` once, then `python -m research_agent.cli check-model` before showing the agent.

## Demo commands

```bat
python -m research_agent.cli chat --memory buffer --session viva_buffer
python -m research_agent.cli compare-memory
python -m research_agent.cli evaluate --limit 100 --output output/final_100
streamlit run app.py
```

The 100-question run is complete. Show the actual values above and use
`output/final_100/comparison.csv` as supporting evidence.

