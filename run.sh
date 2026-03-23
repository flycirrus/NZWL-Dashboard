#!/bin/bash
echo "Starting NZWL Zahlungsplanung & Liquiditätssteuerung..."

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Optional: Create and activate a virtual environment if not present
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing requirements..."
pip install -r requirements.txt

echo "Starting Streamlit App..."
streamlit run dashboard/app.py
