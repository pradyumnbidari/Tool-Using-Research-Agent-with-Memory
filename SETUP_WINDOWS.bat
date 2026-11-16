@echo off
cd /d "%~dp0"
echo Installing the Tool-Using Research Agent...
py -m venv .venv
if errorlevel 1 (
  echo Python Launcher not found. Install Python 3.11 or 3.12 first.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo Package installation failed. Check internet access.
  pause
  exit /b 1
)
if not exist .env copy .env.example .env
echo.
echo Installation done! The free project uses your local Ollama model.
echo You do NOT need any OpenAI API key or credits.
echo Run DOWNLOAD_FREE_MODEL.bat once to download qwen2.5:3b.
echo Then double-click RUN_AGENT.bat or RUN_EVALUATION.bat.
pause

