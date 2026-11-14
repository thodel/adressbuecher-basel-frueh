#!/usr/bin/env python3
"""1841 und 1850 aus thodel/adressbuecher-basel übernehmen (dort mit Gemini gelesen und mit Regeln zerlegt).

    python3 scripts/04_import_basel.py --repo ~/Repos/adressbuecher-basel --commit <sha>

Liest am gepinnten Commit (git show) 02_lines.csv (Lauf basel-gemini-v1, aus dem dort die Einträge stammen),
04_entries.csv (Register = Einwohner), 05_buildings.csv (Nummernbuch: Haus und Eigentümer) und
05_residents.csv (weitere Bewohner im Nummernbuch) und schreibt sie im Schema dieses Repos nach
data/import/basel_{lines,entries,pages}.csv. 03_csv.py hängt sie an. Die Webbilder der übernommenen
Seiten (site/img/<Band>/) erzeugt --images aus den Seitenbildern des Basler Repos (data/pages/, dort
nicht eingecheckt).
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VOLS = ("1841", "1850")
RUN = "basel-gemini-v1"
SECTION = {"einwohner": "register", "gebaeude": "nummernbuch"}


def show(repo: Path, commit: str, path: str) -> list[dict]:
    out = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{path}"], check=True, capture_output=True).stdout
    return list(csv.DictReader(io.StringIO(out.decode("utf-8"))))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=Path.home() / "Repos/adressbuecher-basel")
    ap.add_argument("--commit", required=True)
    ap.add_argument("--images", action="store_true", help="Webbilder der Seiten nach site/img/ schreiben")
    a = ap.parse_args()
    src = f"thodel/adressbuecher-basel@{a.commit[:7]}"
    lines = [r for r in show(a.repo, a.commit, "data/csv/02_lines.csv") if r["volume"] in VOLS and r["run_id"] == RUN]
    ents = [r for r in show(a.repo, a.commit, "data/csv/04_entries.csv") if r["volume"] in VOLS]
    blds = [r for r in show(a.repo, a.commit, "data/csv/05_buildings.csv") if r["volume"] in VOLS]
    res = [r for r in show(a.repo, a.commit, "data/csv/05_residents.csv") if r["volume"] in VOLS]
    pages = {(r["volume"], int(r["page"])): r for r in show(a.repo, a.commit, "data/csv/01_pages.csv") if r["volume"] in VOLS}

    out_e = []
    def add(r, section, kind, surname, forename, title, occ, street, house_no, quarter, house_name, origin, note, text, eid):
        out_e.append({"entry_id": eid, "volume": r["volume"], "page": r["page"], "section": section,
                      "line_from": r.get("line_from") or r.get("line", ""), "line_to": r.get("line_to") or r.get("line", ""),
                      "kind": kind or "person", "heading": r.get("heading", ""), "place": "Basel",
                      "surname": surname, "forename": forename, "title": title, "occupation": occ,
                      "address": " ".join(x for x in (house_no, street) if x), "quarter": quarter, "street": street,
                      "house_no": house_no, "house_name": house_name, "origin": origin, "note": note, "text": text,
                      "reader": "gemini-3.8-flash", "run": f"{RUN} ({src})"})
    for r in ents:
        add(r, SECTION.get(r["section"], r["section"]), r["entry_type"], r["surname"], r["forename"],
            " ".join(x for x in (r["title"], r["civil_status"]) if x), r["occupation_raw"], r["street_raw"],
            r["building_no"], r["city_part"], "", r["origin_raw"],
            "; ".join(x for x in (f"geb. {r['maiden_name']}" if r["maiden_name"] else "", "Name aus Vorzeile" if r["surname_inherited"] else "") if x),
            r["text"], f"{r['entry_id']}")
    for b in blds:
        o = json.loads(b["owner_entry"] or "{}")
        add(b, "nummernbuch", "person" if b["owner_surname"] else "sonst", b["owner_surname"], o.get("forename", ""), o.get("title", ""),
            o.get("occupation_raw", ""), b["street_raw"], b["building_no"], b["quarter"], b["house_name"], "",
            "; ".join(x for x in ("Eigentümer" if b["owner_surname"] else "", b["note"]) if x), b["owner_text"],
            f"{b['building_id']}-E")
    for r in res:
        add(r, "nummernbuch", r["entry_type"], r["surname"], r["forename"], " ".join(x for x in (r["title"], r["civil_status"]) if x),
            r["occupation_raw"], r["street_raw"], r["building_no"], r["city_part"], "", r["origin_raw"], "Bewohner", r["text"], r["entry_id"])

    used = {(e["volume"], int(e["page"])) for e in out_e}
    out_p = []
    for (v, p), r in sorted(pages.items()):
        if (v, p) not in used:
            continue
        out_p.append({"volume": v, "page": p, "section": next(e["section"] for e in out_e if e["volume"] == v and int(e["page"]) == p),
                      "image": "", "web_image": f"img/{v}/p{p:03d}.jpg", "width": r["width"], "height": r["height"],
                      "printed_page": r["printed_page"]})
        if a.images:
            from PIL import Image
            dest = ROOT / "site/img" / v / f"p{p:03d}.jpg"
            if not dest.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                im = Image.open(a.repo / "data/pages" / r["image"]).convert("RGB")
                im.thumbnail((900, 2000)); im.save(dest, quality=60, optimize=True)
    out_l = [{"volume": r["volume"], "page": r["page"], "line": r["line"], "text": r["text"]}
             for r in lines if (r["volume"], int(r["page"])) in used]
    d = ROOT / "data/import"; d.mkdir(parents=True, exist_ok=True)
    for name, rows in (("basel_entries.csv", out_e), ("basel_lines.csv", out_l), ("basel_pages.csv", out_p)):
        with (d / name).open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
        print(f"{name}: {len(rows)}")
    (d / "SOURCE.txt").write_text(f"{src}\nhttps://github.com/thodel/adressbuecher-basel/tree/{a.commit}\n")


if __name__ == "__main__":
    main()
