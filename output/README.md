# Output files

This folder fills automatically during execution:

- `sessions/*.json` - persistent per-session memory data
- `traces/<session>/*.jsonl` - Thought / Action / Observation logs
- `memory_comparison/*.csv, *.json` - three-memory experiment
- `final_100/{react_results.jsonl,cot_results.jsonl,comparison.csv,summary.json,traces/}` - benchmark

API-backed outputs are omitted until a real API key is supplied. **Do not invent or
copy example scores into the report as if they came from the 100-question run.**

