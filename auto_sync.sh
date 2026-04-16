#!/bin/bash

# ============================================
#  NZWL Zahlungsplanung — Auto Sync Script
#  Auf BEIDEN Rechnern gleich verwenden!
# ============================================

# Farben für Terminal-Output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Projektpfad (anpassen falls nötig)
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo ""
echo "============================================"
echo "  NZWL Zahlungsplanung — Auto Sync"
echo "============================================"
echo ""

# ---- SCHRITT 1: Neuesten Stand holen ----
echo -e "${YELLOW}⬇️  Hole neuesten Stand von GitHub...${NC}"

git fetch origin main

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" != "$REMOTE" ]; then
    git pull origin main
    echo -e "${GREEN}✅ Projekt aktualisiert!${NC}"
else
    echo -e "${GREEN}✅ Bereits auf dem neuesten Stand.${NC}"
fi

echo ""

# ---- SCHRITT 2: App starten ----
echo -e "${GREEN}🚀 Starte App...${NC}"
source venv/bin/activate 2>/dev/null || source .venv/bin/activate 2>/dev/null || true
streamlit run dashboard/app.py &
APP_PID=$!
echo -e "${GREEN}   App läuft (PID: $APP_PID)${NC}"
echo ""

# ---- SCHRITT 3: Auto-Sync im Hintergrund ----
echo -e "${YELLOW}🔄 Auto-Sync aktiv (alle 60 Sekunden)${NC}"
echo -e "   Zum Beenden: ${RED}Ctrl+C${NC}"
echo ""

# Cleanup beim Beenden (Ctrl+C)
cleanup() {
    echo ""
    echo -e "${YELLOW}⏹️  Stoppe App und sync ein letztes Mal...${NC}"

    # Letzter Push beim Beenden
    git add -A
    if ! git diff --cached --quiet; then
        git commit -m "Auto-sync (exit): $(date '+%Y-%m-%d %H:%M')"
        git push origin main
        echo -e "${GREEN}☁️  Final-Push erfolgreich!${NC}"
    fi

    kill $APP_PID 2>/dev/null
    echo -e "${GREEN}✅ Tschüss!${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Auto-Sync Loop
while true; do
    sleep 60

    git add -A

    if ! git diff --cached --quiet; then
        TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
        git commit -m "Auto-sync: $TIMESTAMP"

        if git push origin main; then
            echo -e "${GREEN}☁️  [$TIMESTAMP] Änderungen gepusht${NC}"
        else
            echo -e "${RED}❌  Push fehlgeschlagen — Konflikt?${NC}"
            git pull --rebase origin main
            git push origin main
            echo -e "${YELLOW}🔧  Konflikt behoben und gepusht${NC}"
        fi
    fi
done
