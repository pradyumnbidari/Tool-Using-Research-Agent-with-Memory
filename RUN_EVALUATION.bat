@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\activate.bat (
  echo Run SETUP_WINDOWS.bat first.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
echo.
echo WARNING: The full evaluation makes over 200 LOCAL model calls.
echo It is FREE, but may take several hours on a laptop without a strong GPU.
echo Keep Ollama running and make sure the laptop stays awake.
set /p CONFIRM=Type YES to start the local 100-question comparison: 
if /I not "%CONFIRM%"=="YES" exit /b 0
python -m research_agent.cli evaluate --limit 100 --output output/final_100
echo.
echo Compare results in output\final_100\comparison.csv
echo Update PDF with: python scripts\build_report.py
pause

