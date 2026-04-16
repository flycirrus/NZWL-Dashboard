@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: ============================================================
::  NZWL Dashboard — Pull & Run (taeglicher Betrieb)
::  Zieht neuesten Stand von GitHub und startet das Dashboard.
::  Ideal als Autostart oder geplante Aufgabe (Task Scheduler).
::
::  Verzeichnisstruktur (gemaess Server-Spezifikationen):
::    C:\nzwl\
::    ├── app\       (Git-Clone)
::    ├── venv\      (Python venv)
::    ├── data\      (input/dummy/output)
::    ├── logs\
::    ├── backups\
::    └── config\    (.env)
:: ============================================================

title NZWL Dashboard — Pull ^& Run

:: ----- Konfiguration -----
set "BASE_DIR=C:\nzwl"
set "APP_DIR=%BASE_DIR%\app"
set "VENV_DIR=%BASE_DIR%\venv"
set "LOG_DIR=%BASE_DIR%\logs"
set "BRANCH=main"
set "SERVICE_PORT=8501"
set "LOG_FILE=%LOG_DIR%\nzwl_%date:~-4,4%%date:~-7,2%%date:~-10,2%.log"

:: ----- Erstelle Log-Verzeichnis -----
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo ============================================ >> "%LOG_FILE%"
echo  NZWL Pull ^& Run — %date% %time% >> "%LOG_FILE%"
echo ============================================ >> "%LOG_FILE%"

:: ----- Prüfe ob Projekt vorhanden -----
if not exist "%APP_DIR%\.git" (
    echo [FAIL] Projekt nicht gefunden unter %APP_DIR%
    echo        Bitte zuerst deploy_windows.bat ausfuehren!
    echo [FAIL] Projekt nicht gefunden >> "%LOG_FILE%"
    pause
    exit /b 1
)

:: ----- Prüfe ob venv vorhanden -----
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo [FAIL] venv nicht gefunden unter %VENV_DIR%
    echo        Bitte zuerst deploy_windows.bat ausfuehren!
    echo [FAIL] venv nicht gefunden >> "%LOG_FILE%"
    pause
    exit /b 1
)

:: ----- Git Pull -----
echo.
echo [INFO] Hole neuesten Stand von GitHub...
pushd "%APP_DIR%"

git fetch origin %BRANCH% 2>>"%LOG_FILE%"

for /f %%i in ('git rev-parse HEAD') do set LOCAL=%%i
for /f %%i in ('git rev-parse origin/%BRANCH%') do set REMOTE=%%i

if "!LOCAL!" NEQ "!REMOTE!" (
    echo [INFO] Neuer Stand verfuegbar — aktualisiere...
    git pull origin %BRANCH% 2>>"%LOG_FILE%"
    echo [OK]   Applikationscode aktualisiert.
    echo [OK]   Applikationscode aktualisiert >> "%LOG_FILE%"

    :: Bei Updates: Pakete neu installieren
    echo [INFO] Aktualisiere Python-Pakete...
    call "%VENV_DIR%\Scripts\activate.bat"
    pip install -r "%APP_DIR%\requirements.txt" --quiet 2>>"%LOG_FILE%"
    echo [OK]   Pakete aktualisiert.
    echo [OK]   Pakete aktualisiert >> "%LOG_FILE%"
) else (
    echo [OK]   Bereits auf dem neuesten Stand.
    echo [OK]   Bereits aktuell >> "%LOG_FILE%"
)

popd

:: ----- Beende evtl. laufende Streamlit-Instanz -----
echo [INFO] Pruefe auf laufende Streamlit-Instanzen...
taskkill /f /im streamlit.exe >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :%SERVICE_PORT% ^| findstr LISTENING 2^>nul') do (
    taskkill /f /pid %%a >nul 2>&1
)
echo [OK]   Port %SERVICE_PORT% ist frei.

:: ----- Dashboard starten -----
echo.
echo ============================================================
echo.
echo   NZWL Dashboard gestartet!
echo.
echo   Lokal:     http://localhost:%SERVICE_PORT%/NZWL-ZP-MVP
echo   Netzwerk:  http://^<SERVER-IP^>:%SERVICE_PORT%/NZWL-ZP-MVP
echo.
echo   App:       %APP_DIR%
echo   Logs:      %LOG_FILE%
echo.
echo ============================================================
echo.

echo [INFO] Dashboard gestartet um %time% >> "%LOG_FILE%"

pushd "%APP_DIR%"
call "%VENV_DIR%\Scripts\activate.bat"
streamlit run dashboard\app.py
popd
