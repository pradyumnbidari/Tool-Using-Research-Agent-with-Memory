@echo off
cd /d "%~dp0"
where ollama >nul 2>nul
if errorlevel 1 (
  echo Ollama command not found. Install Ollama from https://ollama.com/download/windows
  echo Then close and reopen CMD before running this script.
  pause
  exit /b 1
)
echo Downloading the free qwen2.5:3b model, about 1.9 GB.
echo The model runs on your own computer. No API credits are needed.
ollama pull qwen2.5:3b
if errorlevel 1 (
  echo The model download failed. Check internet connection and try again.
  pause
  exit /b 1
)
echo Model ready! You can now double-click RUN_AGENT.bat.
pause
