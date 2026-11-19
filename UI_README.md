# Research Agent — Web Dashboard

This folder upgrades the existing **Tool-Using Research Agent with Memory** with a polished, interactive Streamlit UI. It uses the **existing Python research agent and local Ollama model**, not a new API or paid service.

## What is included

| File | Where it belongs | What it does |
|---|---|---|
| `app.py` | Project root | Main five-page Streamlit dashboard (replaces the previous basic `app.py`) |
| `ui_theme.css` | Project root | Dark responsive design, chat and dashboard styling |
| `RUN_UI.bat` | Project root | Double-click Windows launcher with setup check |
| `UI_README.md` | Project root | This guide |
| `.env.example` | Project root | Safe local Ollama configuration template; not a secret |

**Do not upload this ZIP itself as your source code.** First extract the ZIP, then upload the five files into the root of your existing repository, next to `requirements.txt`, `SETUP_WINDOWS.bat` and `research_agent/`.

## Manually commit through the GitHub website

1. Open [our GitHub repository](https://github.com/pradyumnbidari/Tool-Using-Research-Agent-with-Memory).
2. Go to the repository main page (not a subfolder).
3. Select **Add file → Upload files**.
4. Drag all five extracted files into GitHub. Confirm `app.py` is replacing the old root file, and the other files are added. If GitHub won't accept replacing an existing filename, open the old `app.py`, click the pencil, and paste in the new `app.py` contents.
5. Enter commit message: `Add interactive research agent dashboard`.
6. Click **Commit changes**.

**Keep these existing project folders untouched:** `research_agent/`, `output/`, `docs/`, `scripts/`, `tests/`, `deliverables/`.

**Never upload:** `.venv/`, your private `.env`, `__pycache__/`, or API keys. `.env.example` is intentionally safe to share.

## Run it on Windows

### If you already have the project working on your laptop

1. Put the new `app.py`, `ui_theme.css`, `RUN_UI.bat` and `UI_README.md` into your existing project folder (`D:\5TH SEM\Prompt\research_agent_project` or whatever folder you currently use).
2. **Keep your existing `.venv`, `.env`, and `output` folders.** No need to delete them or rerun your 100-question evaluation.
3. Double-click **`RUN_UI.bat`**.
4. Open `http://localhost:8501` if your browser does not open automatically.

### If you are downloading the project from GitHub on a new computer

1. Click **Code → Download ZIP** in GitHub and extract the project.
2. Install Python 3.11 or 3.12 and [Ollama](https://ollama.com/).
3. Double-click `DOWNLOAD_FREE_MODEL.bat` (downloads local `qwen2.5:3b`).
4. Double-click `RUN_UI.bat`; it will perform project setup automatically if `.venv` is absent.

The dashboard shows saved **Benchmark Results**, **Memory Lab** and **Trace Explorer** pages even while Ollama is offline. To get new answers in **Research Chat**, start Ollama first.

## Dashboard pages

- **Research Chat:** Ask questions, choose buffer / summary / entity memory, change max tool steps, inspect the step-by-step tool trail, export a trace.
- **Benchmark Results:** Reads `output/final_100/summary.json`, ReAct results, and CoT results from your real 100-question evaluation. Includes charts, individual answers, and CSV export.
- **Memory Lab:** Reads `output/memory_comparison/memory_comparison.json`, compares the three strategies, and shows saved memory snapshots.
- **Trace Explorer:** Opens existing JSONL tool records, including evaluation and new chat sessions.
- **About Project:** Project architecture, team details, and report/presentation downloads when available.

## What to show the panel

1. Start at **About Project** to explain the architecture and tools.
2. Go to **Research Chat**; ask a factual or calculator question and open its tool trace. This requires Ollama running.
3. Open **Benchmark Results** and explain why the actual CoT performance (15% exact match) exceeded ReAct (7%) in this run. These numbers load from your saved data, not from the UI source code.
4. Show **Memory Lab** to explain buffer, summary, and entity recall, and mention the memory test was a small, four-turn illustrative experiment.
5. Show **Trace Explorer** to prove tool actions are logged as JSONL.

## Troubleshooting

| Problem | Try this |
|---|---|
| Ollama offline | Launch Ollama, or run `ollama serve` in a separate Command Prompt. |
| Model not downloaded | Run `DOWNLOAD_FREE_MODEL.bat` or `ollama pull qwen2.5:3b`. |
| Browser didn't open | Visit `http://localhost:8501`. |
| `No module named streamlit` | Activate `.venv` then use `python -m pip install -r requirements.txt`, or double-click `RUN_UI.bat`. |
| Results page has no data | Make sure the downloaded project contains the original `output/final_100/` files, with `summary.json` and both `.jsonl` results files. |
| Trace Explorer empty | Keep your `output/final_100/traces/` folder or generate a fresh chat trace. |
| Different memory modes affect each other | Use a different Session ID for each memory strategy, e.g. `demo_buffer`, `demo_summary`, `demo_entity`. |

### Stack

Python · Streamlit · LangGraph · LangChain · Ollama `qwen2.5:3b` · Wikipedia · HotpotQA
