PY ?= .venv/bin/python
BACKEND ?= qwen
VOL ?= 1789

.PHONY: venv pages smoke read csv site serve
venv:  ## Python-Umgebung
	python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

pages:  ## Seitenliste (01_pages.csv), Lesebilder (data/pages/, nicht im Repo) und Webbilder (site/img/)
	$(PY) scripts/01_pages.py

read:  ## einen Band lesen (VOL=…, BACKEND=qwen|gemini)
	$(PY) scripts/02_read.py --backend $(BACKEND) --run $(BACKEND)-v1 --volume $(VOL) --workers 2

csv:  ## Antworten -> data/csv/ (gemini-v1 ersetzt qwen-v1, wo vorhanden; 1841/1850 aus data/import/)
	$(PY) scripts/03_csv.py --run qwen-v1 --prefer gemini-v1

site: csv  ## Daten für site/ erzeugen
	$(PY) scripts/90_site.py

serve:  ## lokale Vorschau auf http://localhost:8000
	cd site && python3 -m http.server 8000
