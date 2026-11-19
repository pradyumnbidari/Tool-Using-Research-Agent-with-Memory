@echo off
setlocal
cd /d "%~dp0"
title Research Agent - Web UI

echo =======================================================
echo    TOOL-USING RESEARCH AGENT - WEB DASHBOARD
echo =======================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found. Starting initial setup...
    if not exist "SETUP_WINDOWS.bat" (
        echo ERROR: SETUP_WINDOWS.bat not found. Extract/upload the UI
        echo files into the main Research Agent project folder.
        pause
        exit /b 1
    )
    call "SETUP_WINDOWS.bat"
)

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Python environment was not created.
    echo Please check Python installation and run SETUP_WINDOWS.bat.
    pause
    exit /b 1
)

echo Checking Streamlit...
".venv\Scripts\python.exe" -m pip show streamlit >nul 2>&1
if errorlevel 1 (
    echo Installing required Python packages...
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Package installation failed. Check your internet connection.
        pause
        exit /b 1
    )
)

echo.
echo Starting the UI. Your browser should open automatically.
echo If not, open http://localhost:8501
echo Ollama and the qwen2.5:3b model are required only for live chat.
echo.
".venv\Scripts\python.exe" -m streamlit run app.py --server.headless false
if errorlevel 1 (
    echo.
    echo Dashboard stopped with an error. Keep this window open for details.
    pause
)
endlocal
