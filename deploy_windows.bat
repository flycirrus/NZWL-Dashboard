@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: ============================================================
::  NZWL Dashboard — Windows Server Deployment Script
::  Folgt der Verzeichnisstruktur aus NZWL_Server_Spezifikationen
::
::  Struktur:
::    C:\nzwl\
::    ├── app\            (Git-Clone)
::    ├── venv\           (Python Virtual Environment)
::    ├── data\
::    │   ├── input\      (SAP-Exports)
::    │   ├── dummy\
::    │   └── output\
::    ├── logs\
::    ├── backups\
::    └── config\         (.env etc.)
:: ============================================================

title NZWL Dashboard — Server Deployment

echo.
echo ============================================================
echo   NZWL Zahlungsplanung - Windows Server Deployment
echo   Verzeichnis: C:\nzwl
echo ============================================================
echo.

:: ----- Konfiguration -----
set "REPO_URL=https://github.com/flycirrus/NZWL-Dashboard.git"
set "BRANCH=main"
set "BASE_DIR=C:\nzwl"
set "APP_DIR=%BASE_DIR%\app"
set "VENV_DIR=%BASE_DIR%\venv"
set "DATA_DIR=%BASE_DIR%\data"
set "LOG_DIR=%BASE_DIR%\logs"
set "BACKUP_DIR=%BASE_DIR%\backups"
set "CONFIG_DIR=%BASE_DIR%\config"
set "SERVICE_PORT=8501"

:: ============================================================
::  SCHRITT 0: Voraussetzungen pruefen
:: ============================================================
echo [INFO] Pruefe Voraussetzungen...

where git >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [FAIL] Git ist nicht installiert!
    echo        Bitte installiere Git: https://git-scm.com/download/win
    echo        Nach der Installation dieses Skript erneut ausfuehren.
    pause
    exit /b 1
)
echo [OK]   Git gefunden.

where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [FAIL] Python ist nicht installiert!
    echo        Bitte installiere Python 3.10+: https://www.python.org/downloads/
    echo        WICHTIG: Bei der Installation "Add Python to PATH" ankreuzen!
    pause
    exit /b 1
)
echo [OK]   Python gefunden.

:: Python-Version pruefen
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [OK]   Python Version: %PYVER%
echo.

:: ============================================================
::  SCHRITT 1: Verzeichnisstruktur anlegen
:: ============================================================
echo [INFO] Lege Verzeichnisstruktur an...

if not exist "%BASE_DIR%"    mkdir "%BASE_DIR%"
if not exist "%DATA_DIR%\input"  mkdir "%DATA_DIR%\input"
if not exist "%DATA_DIR%\dummy"  mkdir "%DATA_DIR%\dummy"
if not exist "%DATA_DIR%\output" mkdir "%DATA_DIR%\output"
if not exist "%LOG_DIR%"     mkdir "%LOG_DIR%"
if not exist "%BACKUP_DIR%"  mkdir "%BACKUP_DIR%"
if not exist "%CONFIG_DIR%"  mkdir "%CONFIG_DIR%"

echo [OK]   C:\nzwl\
echo        ├── app\            (Git-Clone)
echo        ├── venv\           (Python venv)
echo        ├── data\input\     (SAP-Exports)
echo        ├── data\dummy\
echo        ├── data\output\
echo        ├── logs\
echo        ├── backups\
echo        └── config\         (.env etc.)
echo.

:: ============================================================
::  SCHRITT 2: Repository klonen oder aktualisieren
:: ============================================================
if exist "%APP_DIR%\.git" (
    echo [INFO] App-Verzeichnis existiert bereits. Aktualisiere...
    pushd "%APP_DIR%"
    git fetch origin %BRANCH%
    git reset --hard origin/%BRANCH%
    git pull origin %BRANCH%
    popd
    echo [OK]   Applikationscode aktualisiert.
) else (
    echo [INFO] Klone Repository von GitHub nach app\ ...
    git clone -b %BRANCH% %REPO_URL% "%APP_DIR%"
    if %ERRORLEVEL% NEQ 0 (
        echo [FAIL] Git clone fehlgeschlagen!
        echo        Stelle sicher, dass du Zugang zum Repository hast.
        echo        Falls privat: git config --global credential.helper manager
        pause
        exit /b 1
    )
    echo [OK]   Repository geklont nach %APP_DIR%.
)
echo.

:: ============================================================
::  SCHRITT 3: Virtuelle Umgebung anlegen (ausserhalb von app/)
:: ============================================================
echo [INFO] Pruefe virtuelle Umgebung...

if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo [INFO] Lege venv an: %VENV_DIR%
    python -m venv "%VENV_DIR%"
    if %ERRORLEVEL% NEQ 0 (
        echo [FAIL] venv-Erstellung fehlgeschlagen!
        pause
        exit /b 1
    )
    echo [OK]   venv erstellt.
) else (
    echo [OK]   venv existiert bereits.
)
echo.

:: ============================================================
::  SCHRITT 4: Python-Pakete installieren
:: ============================================================
echo [INFO] Installiere Python-Pakete...

call "%VENV_DIR%\Scripts\activate.bat"

pip install --upgrade pip --quiet
if exist "%APP_DIR%\requirements.txt" (
    pip install -r "%APP_DIR%\requirements.txt" --quiet
    echo [OK]   Alle Pakete aus requirements.txt installiert.
) else (
    echo [WARN] Keine requirements.txt gefunden in %APP_DIR%!
)
echo.

:: ============================================================
::  SCHRITT 5: Streamlit-Konfiguration
:: ============================================================
echo [INFO] Pruefe Streamlit-Konfiguration...

if not exist "%APP_DIR%\.streamlit" (
    mkdir "%APP_DIR%\.streamlit"
)

:: Server-Config fuer headless + Netzwerkzugriff
(
    echo [server]
    echo port = %SERVICE_PORT%
    echo headless = true
    echo address = "0.0.0.0"
    echo baseUrlPath = "NZWL-ZP-MVP"
    echo.
    echo [browser]
    echo gatherUsageStats = false
) > "%APP_DIR%\.streamlit\config.toml"
echo [OK]   Streamlit-Konfiguration geschrieben.
echo.

:: ============================================================
::  SCHRITT 6: .env Template anlegen (falls nicht vorhanden)
:: ============================================================
if not exist "%CONFIG_DIR%\.env" (
    echo [INFO] Erstelle .env Template in config\ ...
    (
        echo # NZWL Dashboard — Umgebungsvariablen
        echo # Bitte anpassen!
        echo.
        echo # MariaDB (optional, fuer spaetere DB-Anbindung)
        echo NZWL_DB_HOST=127.0.0.1
        echo NZWL_DB_PORT=3306
        echo NZWL_DB_NAME=nzwl_db
        echo NZWL_DB_USER=nzwl_app
        echo NZWL_DB_PASS=
        echo.
        echo # Streamlit
        echo NZWL_PORT=%SERVICE_PORT%
        echo.
        echo # Pfade
        echo NZWL_DATA_INPUT=%DATA_DIR%\input
        echo NZWL_DATA_OUTPUT=%DATA_DIR%\output
        echo NZWL_LOG_DIR=%LOG_DIR%
        echo NZWL_BACKUP_DIR=%BACKUP_DIR%
    ) > "%CONFIG_DIR%\.env"
    echo [OK]   .env Template erstellt. Bitte Werte anpassen!
) else (
    echo [OK]   .env existiert bereits in config\.
)
echo.

:: ============================================================
::  SCHRITT 7: Setup-Skript ausfuehren (Systemcheck)
:: ============================================================
echo [INFO] Fuehre Systemcheck aus...
pushd "%APP_DIR%"
"%VENV_DIR%\Scripts\python.exe" setup_nzwl.py --check-only
popd
echo.

:: ============================================================
::  SCHRITT 8: Dashboard starten
:: ============================================================
echo ============================================================
echo.
echo   NZWL Dashboard wird gestartet!
echo.
echo   Lokal:     http://localhost:%SERVICE_PORT%/NZWL-ZP-MVP
echo   Netzwerk:  http://^<SERVER-IP^>:%SERVICE_PORT%/NZWL-ZP-MVP
echo.
echo   Verzeichnisse:
echo     App:     %APP_DIR%
echo     venv:    %VENV_DIR%
echo     Daten:   %DATA_DIR%
echo     Logs:    %LOG_DIR%
echo     Config:  %CONFIG_DIR%
echo.
echo   Zum Beenden: Ctrl+C oder Fenster schliessen
echo.
echo ============================================================
echo.

pushd "%APP_DIR%"
call "%VENV_DIR%\Scripts\activate.bat"
streamlit run dashboard\app.py
popd

pause
