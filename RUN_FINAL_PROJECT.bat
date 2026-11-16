@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "AGENT_PY=.venv\Scripts\python.exe"

if not exist "%AGENT_PY%" (
  echo Python environment is missing. Double-click SETUP_WINDOWS.bat first.
  pause
  exit /b 1
)

:menu
echo.
echo ============================================================
echo  TOOL-USING RESEARCH AGENT - FREE OLLAMA PROJECT
echo ============================================================
echo  1. Check Ollama model
echo  2. Check Wikipedia access
echo  3. Chat with ReAct agent ^(fresh demo session^)
echo  4. Compare buffer, summary and entity memory
echo  5. Run 3-question evaluation pilot
echo  6. Run full 100-question HotpotQA evaluation
echo  7. Rebuild project report using real results
echo  8. Run automated tests
echo  9. Exit
echo.
set "AGENT_CHOICE="
set /p "AGENT_CHOICE=Choose 1-9: "
if "%AGENT_CHOICE%"=="1" goto checkmodel
if "%AGENT_CHOICE%"=="2" goto checkwiki
if "%AGENT_CHOICE%"=="3" goto chat
if "%AGENT_CHOICE%"=="4" goto memory
if "%AGENT_CHOICE%"=="5" goto pilot
if "%AGENT_CHOICE%"=="6" goto full
if "%AGENT_CHOICE%"=="7" goto report
if "%AGENT_CHOICE%"=="8" goto tests
if "%AGENT_CHOICE%"=="9" exit /b 0
echo Invalid choice. Try again.
goto menu

:checkmodel
"%AGENT_PY%" -m research_agent.cli check-model
goto finished

:checkwiki
"%AGENT_PY%" -m research_agent.cli check-wikipedia
goto finished

:chat
"%AGENT_PY%" -m research_agent.cli chat --memory buffer --session final_demo_buffer
goto finished

:memory
"%AGENT_PY%" -m research_agent.cli compare-memory
echo Results: output\memory_comparison\memory_comparison.csv
goto finished

:pilot
"%AGENT_PY%" -m research_agent.cli evaluate --limit 3 --output output/pilot_final
echo Results: output\pilot_final\comparison.csv
goto finished

:full
echo.
echo This runs 100 questions with ReAct and CoT on your own PC.
echo It is FREE, but may take many hours. Keep Ollama running.
set "AGENT_CONFIRM="
set /p "AGENT_CONFIRM=Type YES to continue: "
if /I not "%AGENT_CONFIRM%"=="YES" goto menu
"%AGENT_PY%" -m research_agent.cli evaluate --limit 100 --output output/final_100
echo Results: output\final_100\comparison.csv
goto finished

:report
"%AGENT_PY%" scripts\build_report.py
echo Report: deliverables\Project_Report.pdf
goto finished

:tests
"%AGENT_PY%" -m pytest -q
goto finished

:finished
echo.
echo Press any key to return to the menu.
pause >nul
goto menu
