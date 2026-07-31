@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo NZWL - Pruefung Ueberfaellig-Summe (Faelligkeiten vs. Ueberfaellig-Analyse)
echo.
if not exist "venv\Scripts\python.exe" (
    echo [FAIL] venv nicht gefunden. Bitte zuerst pull_and_run.bat ausfuehren.
    pause
    exit /b 1
)
call "venv\Scripts\activate.bat"
python "tools\check_ueberfaellig.py"
echo.
pause
