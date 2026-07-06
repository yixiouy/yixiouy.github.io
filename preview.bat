@echo off
cd /d "%~dp0"

echo ========================================
echo   1/2  Building HTML from Markdown...
echo ========================================
D:\ProgramData\Anaconda3\python.exe build.py
if %errorlevel% neq 0 (
    echo [FAIL] Build failed! Check errors above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   2/2  Starting local preview...
echo ========================================
echo   Open http://localhost:8000 in your browser
echo   Press Ctrl+C to stop the server
echo ========================================
timeout /t 1 /nobreak >nul
start http://localhost:8000
D:\ProgramData\Anaconda3\python.exe -m http.server 8000
pause
