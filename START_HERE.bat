@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo.
echo ===========================================================
echo  FREE OLLAMA RESEARCH AGENT - ONE-CLICK PROJECT START
echo ===========================================================
echo.

if not exist ".venv\Scripts\python.exe" (
  echo First launch: setting up Python packages in this NEW folder.
  echo This needs internet once, but does not require a paid AI API key.
  call SETUP_WINDOWS.bat
  if errorlevel 1 (
    echo SETUP FAILED. Please check the messages above and try again.
    pause
    exit /b 1
  )
  if not exist ".venv\Scripts\python.exe" (
    echo SETUP FAILED. Please check Python installation and try again.
    pause
    exit /b 1
  )
)

if not exist ".env" copy ".env.example" ".env" >nul
echo Starting the free research-agent project menu...
call RUN_FINAL_PROJECT.bat
