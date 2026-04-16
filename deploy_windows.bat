@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: ============================================================
::  NZWL Dashboard — Windows Server Deployment Script
::  Klont das Repo von GitHub, richtet alles ein und startet.
:: ============================================================

title NZWL Dashboard — Server Deployment

echo.
echo ============================================================
echo   NZWL Zahlungsplanung - Windows Server Deployment
echo ============================================================
echo.

:: ----- Konfiguration (hier anpassen!) -----
set "REPO_URL=https://github.com/flycirrus/NZWL-Dashboard.git"
set "BRANCH=main"
set "INSTALL_DIR=C:\NZWL-ZP-MVP"
set "SERVICE_PORT=8501"

:: ----- Schritt 0: Prüfe Voraussetzungen -----
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
echo.

:: ----- Schritt 1: Repository klonen oder aktualisieren -----
if exist "%INSTALL_DIR%\.git" (
    echo [INFO] Projekt existiert bereits. Aktualisiere...
    pushd "%INSTALL_DIR%"
    git fetch origin %BRANCH%
    git reset --hard origin/%BRANCH%
    git pull origin %BRANCH%
    popd
    echo [OK]   Projekt aktualisiert.
) else (
    echo [INFO] Klone Repository von GitHub...
    git clone -b %BRANCH% %REPO_URL% "%INSTALL_DIR%"
    if %ERRORLEVEL% NEQ 0 (
        echo [FAIL] Git clone fehlgeschlagen!
        echo        Stelle sicher, dass du Zugang zum Repository hast.
        echo        Falls privat: git config --global credential.helper manager
        pause
        exit /b 1
    )
    echo [OK]   Repository geklont.
)
echo.

:: ----- Schritt 2: Setup-Skript ausfuehren (Systemcheck + venv + Pakete) -----
echo [INFO] Fuehre Setup aus...
pushd "%INSTALL_DIR%"
python setup_nzwl.py
if %ERRORLEVEL% NEQ 0 (
    echo [WARN] Setup-Skript meldete Probleme. Pruefe die Ausgabe oben.
)
popd
echo.

:: ----- Schritt 3: Streamlit-Konfiguration -----
echo [INFO] Pruefe Streamlit-Konfiguration...
if not exist "%INSTALL_DIR%\.streamlit" (
    mkdir "%INSTALL_DIR%\.streamlit"
)

:: Erstelle Server-Config falls nicht vorhanden
if not exist "%INSTALL_DIR%\.streamlit\config.toml" (
    echo [INFO] Erstelle Streamlit-Konfiguration...
    (
        echo [server]
        echo port = %SERVICE_PORT%
        echo headless = true
        echo address = "0.0.0.0"
        echo.
        echo [browser]
        echo gatherUsageStats = false
    ) > "%INSTALL_DIR%\.streamlit\config.toml"
    echo [OK]   Konfiguration erstellt.
) else (
    echo [OK]   Konfiguration existiert bereits.
)
echo.

:: ----- Schritt 4: Dashboard starten -----
echo ============================================================
echo   Starte NZWL Dashboard auf Port %SERVICE_PORT%...
echo   Zugriff: http://localhost:%SERVICE_PORT%
echo   Oder im Netzwerk: http://<SERVER-IP>:%SERVICE_PORT%
echo   Zum Beenden: Ctrl+C oder Fenster schliessen
echo ============================================================
echo.

pushd "%INSTALL_DIR%"
call venv\Scripts\activate.bat
streamlit run dashboard\app.py --server.port %SERVICE_PORT% --server.headless true --server.baseUrlPath NZWL-ZP-MVP
popd

pause
