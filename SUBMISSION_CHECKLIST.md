# Final submission checklist

## Already included in this ZIP

- [x] Working LangGraph ReAct implementation with explicit decision/action/observation cycle.
- [x] Wikipedia, calculator and restricted Python tools.
- [x] JSONL trace logger and token usage accounting.
- [x] Buffer, summary and entity memory implementations with saved session state.
- [x] Memory comparison script and CSV/JSON export.
- [x] Real first 100 HotpotQA distractor validation questions and reference answers.
- [x] ReAct versus single-prompt CoT benchmark code, exact match and token F1.
- [x] Unit tests, Windows setup and runnable command-line interface.
- [x] `RUN_FINAL_PROJECT.bat` menu for Windows model checks, chat, memory study, pilot/full evaluation, report and tests.
- [x] Four-page project report PDF and ten-slide viva presentation.
- [x] Viva questions and system architecture Mermaid file.
- [x] All 100 genuine ReAct trace files, containing 491 logged events, with IDs checked against benchmark results.

## Do before final academic submission

- [x] Report and presentation covers list all four student names and SRNs supplied by the team.
- [x] Install Ollama and download `qwen2.5:3b` (verified on user's Windows PC).
- [x] Run `python -m research_agent.cli check-model` successfully.
- [x] Test live Wikipedia retrieval.
- [x] Include measured `output/memory_comparison/memory_comparison.json` (buffer 100%, summary 100%, entity 50% on two recall prompts per mode).
- [x] Run the full local model evaluation on 100 HotpotQA questions per method.
- [x] Confirm `output/final_100/summary.json` contains `"status": "complete"` and 100 evaluations per method.
- [x] Rebuild the report using actual benchmark scores.
- [x] Update the viva slide with actual accuracy, tool-call and token values.
- [ ] Take screenshots showing a chat answer, a JSONL trace, the memory comparison CSV and the benchmark comparison CSV.
- [x] Include all 100 per-question JSONL traces inside `output/final_100/traces`.

**Academic honesty:** The benchmark completed, but ReAct exact-match accuracy was 7%, not 100%. Memory comparison scores reflect only two graded follow-up prompts per mode. Trace files are present; screenshots can be added if faculty requests them.

