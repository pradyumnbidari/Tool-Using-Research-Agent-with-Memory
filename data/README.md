# HotpotQA benchmark input

Running `python -m research_agent.cli download-data` writes `hotpotqa_100.json` here.

The project intentionally does not ship fabricated evaluation questions or scores.
It retrieves 100 actual examples with IDs and gold answers from the publicly
documented `hotpotqa/hotpot_qa`, `distractor`, `validation` split.

The benchmark sends **only question strings** to the two tested methods. It
does not send gold answers, supporting facts or document contexts.

