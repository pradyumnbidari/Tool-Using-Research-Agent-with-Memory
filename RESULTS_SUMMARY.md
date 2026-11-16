# Verified HotpotQA evaluation results

Model: **Qwen2.5 3B**, run locally with Ollama on 16 November 2026.

Dataset: First 100 rows of HotpotQA distractor validation. The same 100 questions
were submitted to ReAct and the single-prompt CoT baseline. Gold answers were
used only for evaluation.

| Metric | ReAct | CoT baseline |
| --- | ---: | ---: |
| Questions evaluated | 100 | 100 |
| Execution failures | 0 | 0 |
| Normalized exact-match accuracy | **7.0%** | **15.0%** |
| Token F1 | 7.82% | 20.94% |
| Average tool calls per question | 3.91 | 0 |
| Average total tokens per question | 7,371.6 | 166.7 |
| Total measured tokens | 737,164 | 16,666 |
| Abstentions | 82 | 0 |

ReAct status breakdown: 18 completed answers, 53 tool-step-limit outcomes,
29 unverified outcomes. The evaluation correctly counts all 100 ReAct attempts,
including abstentions, in the accuracy denominator. An attempted query that
abstained is not treated as correct or excluded from accuracy.

## Interpretation for viva

In this particular experiment, the **CoT baseline performed better** than the
tool-using agent. CoT answered 15 of 100 questions exactly, versus 7 of 100 for
ReAct. The ReAct system made 3.91 tool calls per question and used many more
tokens because it repeatedly searched, calculated and reviewed observations.
Strict evidence checks also produced 82 abstentions. The results suggest that
the small Qwen2.5 3B model struggled to coordinate several tool steps and
live retrieval. This does **not** establish that ReAct is always worse than CoT.

## Sources and limitations

All numerical results come from the supplied `output/final_100/summary.json`,
`comparison.csv`, `react_results.jsonl` and `cot_results.jsonl`. Both result
files contain exactly 100 distinct question IDs and the same question set.
Historical Wikipedia content may differ from the original HotpotQA evidence.
The numerical scores are not invented or extrapolated from the 3-question pilot.

## Measured four-turn memory comparison

| Memory | Correct recalls | Recall accuracy | Combined tokens | Memory update tokens |
| --- | ---: | ---: | ---: | ---: |
| Buffer | 2 / 2 | 100% | 11,147 | 0 |
| Summary | 2 / 2 | 100% | 10,919 | 480 |
| Entity | 1 / 2 | 50% | 28,023 | 609 |

Buffer retained full conversation history. Summary kept a rolling model-written
summary and used slightly fewer combined tokens than buffer in this tiny test.
Entity used the most tokens and missed one recall. The memory comparison has
only two graded follow-up questions per mode; it is not a statistically reliable
ranking of memory strategies and is separate from the 100-question HotpotQA test.

**Verified trace evidence:** The submission includes 100 per-question
Thought-Action-Observation JSONL files in `output/final_100/traces/`, with
491 total logged events. All 100 filenames match the corresponding ReAct
question IDs in `react_results.jsonl`; every JSONL record parses and its
`run_id` matches its filename. These logs document model/tool behavior,
including repeated searches and abstentions, rather than claiming every
answer was correct.
