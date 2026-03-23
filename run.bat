@echo off
echo Starting NZWL Zahlungsplanung & Liquiditätssteuerung...

cd /d "%~dp0"

IF NOT EXIST "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing requirements...
pip install -r requirements.txt

echo Starting Streamlit App...
streamlit run dashboard\app.py
pause
