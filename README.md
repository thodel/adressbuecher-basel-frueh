# Frühe Basler Adressbücher 1789–1850

Sechs gedruckte Verzeichnisse der Stadt Basel aus dem Staatsarchiv Basel-Stadt (Digitaler Lesesaal, gemeinfrei),
maschinell gelesen und als durchsuchbare statische Seite aufbereitet: <https://thodel.github.io/adressbuecher-basel-frueh/>.
Gegenstück zu den [frühen Berner Adressbüchern](https://github.com/thodel/adressbuecher-bern-frueh).

| Band | Titel | Signatur | gelesene PDF-Seiten | Lesung |
|---|---|---|---|---|
| 1789 | Basler Handlungs-Schema | [STA H 43 1](https://dls.staatsarchiv.bs.ch/records/1225910) | 11–34 | qwen3.8 |
| 1800 | Basler Handlungs-Schema, vierte Auflage | [STA H 43 4](https://dls.staatsarchiv.bs.ch/records/1231732) | 11–28 | qwen3.8 |
| 1811 | Verzeichnis sämmtlicher Häuser und Gebäude | [STA H 43 8](https://dls.staatsarchiv.bs.ch/records/1231736) | 14–266 | Gemini 3.5 Flash, sonst qwen3.8 |
| 1834 | Neues Nummern-Büchlein | [STA H 43 14](https://dls.staatsarchiv.bs.ch/records/1225916) | 14–219, 234–247, 250–314 | Gemini 3.5 Flash, sonst qwen3.8 |
| 1841 | Adressbuch der Stadt Basel | [STA H 43 17](https://dls.staatsarchiv.bs.ch/records/1225921) | übernommen | aus [adressbuecher-basel](https://github.com/thodel/adressbuecher-basel) |
| 1850 | Adressbuch der Stadt Basel | [STA H 43 20](https://dls.staatsarchiv.bs.ch/records/1225925) | übernommen | aus [adressbuecher-basel](https://github.com/thodel/adressbuecher-basel) |

Seitenschlüssel ist die PDF-Seite der Datei aus dem Digitalen Lesesaal (PDF-Seite 1 = Deckblatt des Staatsarchivs).
Abschnitte: `config/volumes.json`. 1841 und 1850 sind im Projekt Adressbücher Basel gelesen und zerlegt und hier
unverändert übernommen (`scripts/04_import_basel.py`, Quelle und Commit in `data/import/SOURCE.txt`).

## Ablauf: ein Band pro Woche

Die Lesung läuft absichtlich langsam: `scripts/weekly.sh` liest jede Woche den nächsten ungelesenen Band (1789,
1800, 1811, 1834), baut CSV und Seite und pusht; GitHub Actions veröffentlicht die Seite. Er läuft als cron-Job
auf tei.dh.unibe.ch (im Netz der Universität, wo der GPUStack erreichbar ist); Protokoll in `data/weekly.log`.

- **Modelle:** `qwen3.8-27b` auf dem GPUStack der Universität Bern. In einer Probe (14.11.2026) las qwen die
  Antiqua-Seiten 1789/1800 fast fehlerfrei, auf einer Fraktur-Tabelle 1811 aber 5 von 34 Familiennamen falsch und
  ordnete die Strassen falsch zu. Für 1811 und 1834 nimmt der Lauf darum Google `gemini-3.5-flash`, wenn in `.env`
  ein Schlüssel liegt und Gemini antwortet (Ausgabenlimit); sonst qwen3.8 mit Vermerk im Protokoll.
- Eine Seite zählt nur, wenn die Antwort regulär endet, als JSON parst, `complete: true` trägt und alle
  Zeilenverweise stimmen (`data/csv/03_page_status.csv`); sonst wird sie wiederholt.

```
make venv                   # Python-Umgebung
make pages                  # 01_pages.csv, Lesebilder (data/pages/, nicht im Repo) und Webbilder (site/img/)
scripts/02_read.py --backend qwen --run qwen-v1 --volume 1789 --workers 2
scripts/03_csv.py --run qwen-v1 --prefer gemini-v1 && scripts/90_site.py
make serve                  # Vorschau
```

Schlüssel: GPUStack über `GPUSTACK_BASE_URL`/`GPUSTACK_API_KEY` in der Umgebung, Gemini über `GEMINI_API_KEY` in
der Umgebung oder in `.env` (nicht eingecheckt). Prompt `prompts/entries.md`, Bandhinweise `config/hints.json`.

## Daten

`data/csv/`, Schema in `docs/schema.md` (wie bei den frühen Berner Adressbüchern, dazu `house_name`).
Rohantworten in `data/raw/<lauf>/<band>/`. Die Seite (`site/`) ist statisch; die Seitenbilder liegen verkleinert
in `site/img/`.

1811 und 1834 sind durchschossene Exemplare mit vielen handschriftlichen Nachträgen; gelesen wird nur das
Gedruckte, von Hand gestrichene gedruckte Namen tragen den Vermerk «gestrichen (Hand)».

## Lizenz

Die Vorlagen sind gemeinfrei (Staatsarchiv Basel-Stadt). Daten CC0 1.0, Code MIT.
