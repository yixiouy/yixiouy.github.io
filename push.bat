@echo off
cd /d e:\code\website\my-site

echo ========================================
echo   1/3  Building HTML from Markdown...
echo ========================================
D:\ProgramData\Anaconda3\python.exe build.py
if %errorlevel% neq 0 (
    echo [FAIL] Build failed! Check errors above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   2/3  Committing changes...
echo ========================================
git add -A
git commit -m "Update site content"
if %errorlevel% neq 0 (
    echo [WARN] Nothing to commit or commit failed.
)

echo.
echo ========================================
echo   3/3  Pushing to GitHub...
echo ========================================
git push
if %errorlevel% neq 0 (
    echo [FAIL] Push failed! Check your network.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   [OK] Site published!
echo   Visit https://yixiouy.github.io/
echo ========================================
pause
