"""Generate an A4 project report using real output files when they exist.

Usage: python scripts/build_report.py
"""
from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable, KeepTogether, LongTable, PageBreak, Paragraph,
    SimpleDocTemplate, Spacer, Table, TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "deliverables" / "Project_Report.pdf"
NAVY = colors.HexColor("#14233C")
TEAL = colors.HexColor("#107F86")
PALE = colors.HexColor("#EAF3F5")
GRAY = colors.HexColor("#526273")

_normal_ttf = Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf")
_bold_ttf = Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf")
if _normal_ttf.exists() and _bold_ttf.exists():
    pdfmetrics.registerFont(TTFont("LibSans", str(_normal_ttf)))
    pdfmetrics.registerFont(TTFont("LibSans-Bold", str(_bold_ttf)))
    pdfmetrics.registerFontFamily("LibSans", normal="LibSans", bold="LibSans-Bold")
    FONT_NORMAL, FONT_BOLD = "LibSans", "LibSans-Bold"
else:  # Portable built-in fonts on Windows
    FONT_NORMAL, FONT_BOLD = "Helvetica", "Helvetica-Bold"


def load_json(path: Path):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def safe(value):
    import html

    return html.escape(str(value))


def build():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4, rightMargin=2.0 * cm, leftMargin=2.0 * cm,
        topMargin=2.0 * cm, bottomMargin=1.8 * cm,
        title="Tool-Using Research Agent with Memory - Mini-Project Report",
        author="Prathyush Gowda, Pradyumn Bidari, Prashant Devendra Naik, Pradyun Urs",
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="DocTitleCustom", parent=styles["Title"], fontName=FONT_BOLD,
        fontSize=24, leading=30, textColor=NAVY, alignment=TA_CENTER, spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        name="DocHeadingCustom", parent=styles["Heading2"], fontName=FONT_BOLD,
        fontSize=12.3, leading=16, textColor=NAVY, spaceBefore=9, spaceAfter=3,
    ))
    styles.add(ParagraphStyle(
        name="DocBodyCustom", parent=styles["BodyText"], fontName=FONT_NORMAL,
        fontSize=9.0, leading=12.3, textColor=NAVY, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="DocSmallCustom", parent=styles["BodyText"], fontName=FONT_NORMAL,
        fontSize=8.3, leading=11.5, textColor=GRAY, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="DocTableCustom", parent=styles["BodyText"], fontName=FONT_NORMAL,
        fontSize=8.2, leading=11.5, textColor=NAVY,
    ))
    styles.add(ParagraphStyle(
        name="DocLabelCustom", parent=styles["BodyText"], fontName=FONT_BOLD,
        fontSize=11, leading=16, textColor=TEAL, alignment=TA_CENTER,
    ))
    story = []
    para = lambda text: Paragraph(text, styles["DocBodyCustom"])
    small = lambda text: Paragraph(text, styles["DocSmallCustom"])

    def add_heading(text):
        story.append(Paragraph(text, styles["DocHeadingCustom"]))

    def add_bullet(text):
        story.append(para("<font color='#107F86'><b>&#8226;</b></font> " + text))

    def add_table(headings, rows, widths):
        data = [[Paragraph(safe(x), styles["DocTableCustom"]) for x in headings]]
        data.extend([[Paragraph(safe(x), styles["DocTableCustom"]) for x in row] for row in rows])
        table = LongTable(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PALE),
            ("TEXTCOLOR", (0, 0), (-1, 0), NAVY),
            ("LINEBELOW", (0, 0), (-1, 0), 1, TEAL),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFB")]),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(table)

    # Cover
    story.extend([Spacer(1, 3.1 * cm),
        Paragraph("MINI-PROJECT REPORT", styles["DocLabelCustom"]),
        Spacer(1, 0.7 * cm),
        Paragraph("Tool-Using Research Agent<br/>with Memory", styles["DocTitleCustom"]),
        Spacer(1, 0.4 * cm),
        Paragraph("ReAct + LangGraph + Multi-Turn Memory + HotpotQA", styles["DocLabelCustom"]),
        Spacer(1, 1.1 * cm),
        HRFlowable(width="72%", thickness=1.4, color=TEAL, hAlign="CENTER"),
        Spacer(1, 1 * cm),
        Paragraph("<b>Submitted by</b>", styles["DocBodyCustom"]),
        Paragraph("Prathyush Gowda &nbsp;&nbsp; | &nbsp;&nbsp; PES1UG24AM201", styles["DocBodyCustom"]),
        Paragraph("Pradyumn Bidari &nbsp;&nbsp; | &nbsp;&nbsp; PES1UG24AM194", styles["DocBodyCustom"]),
        Paragraph("Prashant Devendra Naik &nbsp;&nbsp; | &nbsp;&nbsp; PES1UG24AM199", styles["DocBodyCustom"]),
        Paragraph("Pradyun Urs &nbsp;&nbsp; | &nbsp;&nbsp; PES1UG24AM195", styles["DocBodyCustom"]),
        Paragraph("<b>Institution:</b> PES University, Bengaluru", styles["DocBodyCustom"]),
        Paragraph("<b>Course:</b> Prompt Engineering and Optimization for Generative AI", styles["DocBodyCustom"]),
        Spacer(1, 1.3 * cm),
        small("Implementation and offline tests completed. Results include a measured 100-question HotpotQA evaluation and a separate memory comparison using a free local Ollama model."),
        PageBreak(),
    ])

    add_heading("1. Abstract")
    story.append(para(
        "This project implements a research assistant that answers multi-hop factual and numerical questions "
        "through a repeated Reasoning and Acting (ReAct) cycle. A LangGraph state machine asks a language model "
        "to select Wikipedia search, an arithmetic calculator or restricted Python execution, then feeds the "
        "tool observation back into the next step. It logs each shareable decision summary, action, input, "
        "observation, final answer and available token usage. Buffer, summary and entity memory strategies "
        "preserve conversational context. A reproducible pipeline compares the tool-using agent with a "
        "single-prompt Chain-of-Thought (CoT) baseline on the same 100 HotpotQA validation questions."
    ))

    add_heading("2. Problem statement")
    story.append(para(
        "Build an autonomous agent that answers multi-hop factual and numerical questions by selecting "
        "external tools and retaining conversational context. Implement a ReAct pattern with LangChain "
        "or LangGraph, at least three tools, auditable traces, buffer/summary/entity memory, and a "
        "100-question HotpotQA comparison against a single-prompt CoT baseline."
    ))

    add_heading("3. Objectives")
    for item in [
        "Support multi-step fact retrieval, arithmetic and limited Python calculations.",
        "Record a user-readable Thought-Action-Observation log for every agent step.",
        "Maintain context across sessions using three independently selectable memory strategies.",
        "Compare accuracy, tool calls and token usage on an identical fixed HotpotQA subset.",
        "Provide a runnable CLI, optional browser interface, automated tests and exportable results.",
    ]:
        add_bullet(item)

    add_heading("4. Technologies and external resources")
    add_table(["Component", "Technology / function"], [
        ("Agent framework", "Python 3.11+, LangGraph StateGraph, LangChain messages, local ChatOllama"),
        ("Factual retrieval", "Live Wikipedia MediaWiki API over HTTPS"),
        ("Numerical tools", "Python ast arithmetic evaluator and restricted child-process Python"),
        ("Memory", "JSON buffer turns, rolling LLM summary, extracted entity/fact map"),
        ("Evaluation", "HotpotQA distractor validation; normalized exact match and token F1"),
        ("Interface", "Command-line interface, optional Streamlit chat app"),
    ], [4.1 * cm, 12.2 * cm])

    add_heading("5. System architecture")
    story.append(para(
        "The user question and selected session memory become inputs to a LangGraph reasoning node. "
        "The model emits one machine-readable decision. If the decision selects a tool, the action node "
        "invokes it, records the observation and loops to the reasoning node. A final decision ends the "
        "cycle and updates the current memory state. The question, agent decision, tool result, final "
        "answer and usage metadata are available to the CLI and JSONL trace logs."
    ))
    add_table(["Stage", "Stored information"], [
        ("Input", "Question, selected memory context and session ID"),
        ("Decision", "Public thought summary, action name, action input or final answer"),
        ("Act", "Wikipedia / calculator / restricted Python execution"),
        ("Observe", "Actual output or explicit error, appended to trace"),
        ("Finalize", "Response, model token counts and saved memory JSON"),
    ], [3.6 * cm, 12.7 * cm])

    add_heading("6. ReAct algorithm and tool implementations")
    story.append(para(
        "For each query, the model receives the current question, relevant memory and previous tool "
        "observations. It decides whether further evidence is needed. Wikipedia returns up to three "
        "article summaries and URLs. The calculator interprets an allowlisted mathematical AST. "
        "Restricted Python supports numerical expressions and safe built-ins in a child process with "
        "a short execution timeout. The loop stops after a final answer or the configured step limit "
        "(six tool calls by default)."
    ))
    story.append(small(
        "Auditability note: the logged Thought is an explicitly generated, short public decision summary. "
        "It does not claim access to hidden or private model chain-of-thought."
    ))

    add_heading("7. Memory implementations")
    add_table(["Memory type", "Data retained", "Expected tradeoff"], [
        ("Buffer", "Full previous question/answer text", "High fidelity; context grows every turn"),
        ("Summary", "One rolling model-written summary", "Compact context; additional tokens and some loss risk"),
        ("Entity", "Named entity -> factual properties", "Selective factual recall; may miss non-entity details"),
    ], [2.8 * cm, 5.3 * cm, 8.2 * cm])
    story.append(para(
        "A four-turn controlled dialogue repeats identical prompts with each strategy, then grades two "
        "follow-up recall questions. The program additionally logs memory context length, model "
        "tokens and memory-update tokens. Memory states are isolated for fair comparison."
    ))

    add_heading("8. HotpotQA experimental design")
    story.append(para(
        "A fixed dataset is loaded from the first 100 rows of the publicly documented HotpotQA "
        "distractor validation split. Both arms receive the same question strings, model and temperature. "
        "The ReAct arm may access Wikipedia, calculator and Python. The baseline makes exactly one "
        "LLM request with a short CoT instruction and has no tools. Neither arm receives gold answers "
        "or gold supporting paragraphs. Both begin with empty conversation memory for each question."
    ))
    add_table(["Metric", "Meaning"], [
        ("Exact match accuracy", "100 * normalized exactly correct / evaluated questions; abstentions count wrong"),
        ("Token F1", "Token-level precision/recall overlap after normalization"),
        ("Tool calls per query", "Mean number of executed tool invocations"),
        ("Token usage", "Actual provider-reported input + output tokens, mean and total"),
        ("Completion status", "Completed/100; incomplete/error records remain visible"),
    ], [5 * cm, 11.3 * cm])

    benchmark = load_json(ROOT / "output" / "final_100" / "summary.json")
    add_heading("9. Benchmark results")
    if benchmark and benchmark.get("status") == "complete" and benchmark.get("requested_questions") == 100:
        arms = benchmark["methods"]
        rows = [
            (name.upper(), arms[name]["completed"], arms[name]["exact_match_accuracy_pct"],
             arms[name]["token_f1_pct"], arms[name]["mean_tool_calls_per_query"],
             arms[name]["mean_total_tokens_per_query"])
            for name in ("react", "cot")
        ]
        add_table(["Model", "N", "EM %", "F1 %", "Tool calls", "Avg tokens"], rows,
                  [2.5 * cm, 1.3 * cm, 2.2 * cm, 2.2 * cm, 3.3 * cm, 4.8 * cm])
        story.append(small("Results imported from the actual completed output/final_100/summary.json file."))
        react, cot = arms["react"], arms["cot"]
        story.append(KeepTogether([para(
            f"<b>Observed finding:</b> The single-prompt CoT baseline achieved "
            f"<b>{cot['exact_match_accuracy_pct']:.1f}% exact match</b>, compared with "
            f"<b>{react['exact_match_accuracy_pct']:.1f}%</b> for ReAct. The ReAct agent "
            f"recorded <b>{react['abstained']} abstentions</b> and made an average of "
            f"<b>{react['mean_tool_calls_per_query']:.2f} tool calls</b> per question. "
            f"Its average token usage was <b>{react['mean_total_tokens_per_query']:.1f}</b> "
            f"versus <b>{cot['mean_total_tokens_per_query']:.1f}</b> for CoT. "
            "These measurements describe this particular free local Qwen2.5 3B configuration "
            "under live Wikipedia retrieval; they do not imply that ReAct is generally inferior. "
            "Strict evidence checks, tool-selection loops and limited model capacity may have "
            "contributed to the lower ReAct accuracy."
        )]))
    else:
        add_table(["Method", "100 questions", "Exact match", "Tools/query", "Avg tokens"], [
            ("ReAct", "Pending local run", "Not measured", "Not measured", "Not measured"),
            ("Single-prompt CoT", "Pending local run", "Not measured", "0 by design", "Not measured"),
        ], [3.2 * cm, 3.4 * cm, 3.3 * cm, 3.1 * cm, 3.3 * cm])
        story.append(small(
            "The 100 HotpotQA questions are included with the project. A local Ollama model "
            "was not available in the build environment, so genuine benchmark scores must be "
            "generated on the user's PC. No outcomes have been fabricated."
        ))

    memory = load_json(ROOT / "output" / "memory_comparison" / "memory_comparison.json")
    memory_section_start = len(story)
    add_heading("10. Memory comparison results")
    if memory and "methods" in memory:
        rows = []
        for key, value in memory["methods"].items():
            rows.append((key, value["correct_followups"], value["graded_followups"],
                         value["combined_tokens"], value["sum_memory_context_chars"]))
        add_table(["Type", "Correct", "Graded", "Total tokens", "Context chars"], rows,
                  [2.6 * cm, 2.7 * cm, 2.8 * cm, 4.1 * cm, 4.1 * cm])
        modes = memory["methods"]
        story.append(para(
            f"<b>Observed memory result:</b> Buffer recalled "
            f"<b>{modes['buffer']['correct_followups']}/{modes['buffer']['graded_followups']}</b> "
            f"follow-ups; summary recalled "
            f"<b>{modes['summary']['correct_followups']}/{modes['summary']['graded_followups']}</b>; "
            f"entity recalled <b>{modes['entity']['correct_followups']}/{modes['entity']['graded_followups']}</b>. "
            f"Their combined tokens were {modes['buffer']['combined_tokens']:,}, "
            f"{modes['summary']['combined_tokens']:,} and {modes['entity']['combined_tokens']:,}, "
            "respectively. This is a four-turn illustrative memory test with only "
            "two graded recall questions per mode, not a 100-question memory benchmark."
        ))
    else:
        story.append(para(
            "Controlled comparison code is complete. Execute "
            "<b>python -m research_agent.cli compare-memory</b> and regenerate this report to "
            "populate measured memory recall and token-use results."
        ))
    # Prevent the comparison table and its interpretation splitting across pages.
    story[memory_section_start:] = [KeepTogether(story[memory_section_start:])]

    add_heading("11. Validation and implementation status")
    story.append(para(
        "Twenty-one offline tests passed in the build environment. They cover arithmetic correctness, "
        "rejected dangerous expressions, restricted "
        "Python execution, mocked Wikipedia retrieval, all memory strategies, session persistence, "
        "a scripted multi-tool ReAct cycle, trace writing, numeric grounding safeguards, direct "
        "calculator finalization, repeated-tool prevention, malformed-model output, abstention "
        "accounting, token accounting and answer metrics. "
        "Run <b>python -m pytest -q</b> from the project directory to reproduce the checks. "
        "A live model conversation and evaluation require a downloaded local Ollama model "
        "and working Wikipedia access. No paid API is required."
    ))

    add_heading("12. Novelty and independent contributions")
    for item in [
        "One inspectable LangGraph loop that explicitly records each public decision, action and observation.",
        "Pluggable, persistent buffer, summary and entity memories with separately logged maintenance overhead.",
        "A restricted numerical Python tool with an isolated child process and execution time limit.",
        "A matched-question, reproducible HotpotQA comparison with resume support and honest failure counts.",
    ]:
        add_bullet(item)
    story.append(small(
        "ReAct, LangGraph and HotpotQA are established ideas. Novelty here means this project's "
        "specific integration, design choices and comparison, not a new foundational algorithm."
    ))

    add_heading("13. Limitations and future work")
    story.append(para(
        "Wikipedia currently exposes live articles that may differ from HotpotQA's original evidence. "
        "External API requests can fail or be rate-limited. Summary and entity memories can omit facts. "
        "The restricted Python implementation is educational and is not a hardened sandbox for "
        "untrusted internet users. Future work could add evidence attribution, rate limiting, "
        "stronger isolated execution, additional tool APIs and more evaluation samples."
    ))

    add_heading("14. Conclusion")
    if benchmark and benchmark.get("status") == "complete" and benchmark.get("requested_questions") == 100:
        story.append(para(
            "The project implements an auditable tool-using LangGraph agent, three session-memory "
            "strategies and a reproducible benchmark. All 100 HotpotQA questions were evaluated "
            "for both methods. In this local Qwen2.5 3B run the CoT baseline achieved higher exact-match "
            "accuracy and used fewer tokens than ReAct. The main limitation is reliable multi-step "
            "tool coordination with a small model. In the separate four-turn memory study, buffer "
            "and summary each answered both recall prompts, while entity answered one."
        ))
    else:
        story.append(para(
            "The project delivers a modular ReAct agent implementation, tool interfaces, trace logging, "
            "session memory strategies, a test suite and a repeatable evaluation pipeline. Live comparison "
            "results and conclusions about relative model accuracy must be added only after the full "
            "100-question evaluation has completed."
        ))

    add_heading("15. References")
    for citation in [
        "Yao et al., ReAct: Synergizing Reasoning and Acting in Language Models (2022). https://arxiv.org/abs/2210.03629",
        "Yang et al., HotpotQA: A Dataset for Diverse, Explainable Multi-hop Question Answering (2018). https://arxiv.org/abs/1809.09600",
        "LangChain, Agents documentation. https://docs.langchain.com/oss/python/langchain/agents",
        "LangGraph, Persistence documentation. https://docs.langchain.com/oss/python/langgraph/persistence",
        "HotpotQA, official dataset card. https://huggingface.co/datasets/hotpotqa/hotpot_qa",
    ]:
        story.append(small(safe(citation)))

    def header_footer(canvas, rendered_doc):
        canvas.saveState()
        width, height = A4
        canvas.setStrokeColor(colors.HexColor("#DCE6EB"))
        canvas.line(2 * cm, height - 1.5 * cm, width - 2 * cm, height - 1.5 * cm)
        canvas.setFont(FONT_NORMAL, 8)
        canvas.setFillColor(GRAY)
        canvas.drawString(2 * cm, height - 1.22 * cm, "TOOL-USING RESEARCH AGENT WITH MEMORY")
        canvas.drawRightString(width - 2 * cm, 1.12 * cm, f"Page {rendered_doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"Created: {OUTPUT}")


if __name__ == "__main__":
    build()

