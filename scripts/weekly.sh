#!/bin/bash
# Wöchentlicher Lauf (cron auf tei.dh.unibe.ch): liest den nächsten noch nicht gelesenen Band, baut CSV und
# Seite und pusht. Ein Band pro Woche, absichtlich langsam (2 Worker).
#   Reihenfolge: 1789, 1800 (Antiqua, qwen3.8), 1811, 1834 (Fraktur: Gemini 3.5 Flash, wenn ein Schlüssel in .env
#   liegt und Gemini antwortet; sonst qwen3.8 mit Vermerk im Log).
# Schlüssel: GPUStack aus /home/dh/agentic_historian/.env.gpustack, Gemini aus .env im Repo; nie ausgegeben.
set -u
cd "$(dirname "$0")/.."
ts() { TZ=Europe/Zurich date "+%d.%m.%Y %H:%M"; }
log() { echo "$(ts) $*" >> data/weekly.log; echo "$(ts) $*"; }
set -a; . /home/dh/agentic_historian/.env.gpustack 2>/dev/null; set +a
PY=${PY:-python3}
git pull -q --ff-only || { log "FEHLER: git pull"; exit 1; }

done_vol() {  # alle Seiten des Bandes gültig gelesen (in irgendeinem Lauf)?
  $PY - "$1" <<'PYEOF'
import csv, json, sys
from pathlib import Path
v = sys.argv[1]
pages = [int(r["page"]) for r in csv.DictReader(open("data/csv/01_pages.csv")) if r["volume"] == v]
def ok(p):
    for run in Path("data/raw").glob("*"):
        f = run / v / f"p{p:03d}.json"
        if f.exists() and json.loads(f.read_text()).get("ok"):
            return True
    return False
sys.exit(0 if all(ok(p) for p in pages) else 1)
PYEOF
}

vol=""
for v in 1789 1800 1811 1834; do done_vol "$v" || { vol=$v; break; }; done
[ -z "$vol" ] && { log "alle Bände gelesen, nichts zu tun"; exit 0; }

backend=qwen
case $vol in 1811|1834)
  if [ -f .env ] && $PY - <<'PYEOF' >/dev/null 2>&1
import os, sys
from pathlib import Path
k = [l.split("=", 1)[1].strip().strip('"\'') for l in Path(".env").read_text().splitlines() if l.startswith("GEMINI_API_KEY")][0]
from google import genai
c = genai.Client(api_key=k)
c.models.generate_content(model="gemini-3.5-flash", contents="OK")
PYEOF
  then backend=gemini; else log "$vol: Gemini nicht verfügbar (kein Schlüssel oder Ausgabenlimit), lese mit qwen3.8; zur Neulesung vormerken"; fi;;
esac
run=$backend-v1
log "start $vol mit $backend ($run)"
$PY scripts/02_read.py --backend "$backend" --run "$run" --volume "$vol" --workers 2 >> "data/$run.log" 2>&1
# zweiter Versuch für Seiten, die am Netz oder an der Länge scheiterten
$PY scripts/02_read.py --backend "$backend" --run "$run" --volume "$vol" --workers 1 >> "data/$run.log" 2>&1
$PY scripts/03_csv.py --run qwen-v1 --prefer gemini-v1 >> data/weekly.log 2>&1 && $PY scripts/90_site.py >> data/weekly.log 2>&1 || { log "FEHLER: CSV/Seite"; exit 1; }
n=$(awk -F, -v v="$vol" '$1==v && $4=="ok"' data/csv/03_page_status.csv | wc -l)
t=$(awk -F, -v v="$vol" '$1==v' data/csv/03_page_status.csv | wc -l)
log "done $vol: $n von $t Seiten gültig ($backend)"
git add data/raw data/csv data/weekly.log "data/$run.log" site/data site/nav.css site/fieldsearch.js site/index.html site/methoden.html
git commit -q -m "Wöchentliche Lesung: Band $vol mit $backend ($n von $t Seiten)" && git push -q || log "FEHLER: commit/push"
