#!/usr/bin/env python3
"""Stufe 1: Seitenliste und Seitenbilder aus den PDFs des Staatsarchivs Basel-Stadt.

Liest config/volumes.json und schreibt für jede gewählte PDF-Seite
  data/pages/<band>/p<NNN>.jpg   Lesebild, 150 dpi (nicht im Repo, siehe .gitignore)
  site/img/<band>/p<NNN>.jpg     Bild für die Seite, 900 px breit (im Repo; die Bände sind gemeinfrei)
und data/csv/01_pages.csv. Seitenschlüssel ist die PDF-Seite (1-basiert); PDF-Seite 1 ist das Deckblatt
des Staatsarchivs. PDF-Ordner: --pdf-dir oder ~/Documents/Adressbuch-Sammlung/basel_frueh/.
Bereits vorhandene Bilder werden nicht neu erzeugt.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    import pymupdf
    from PIL import Image

    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf-dir", type=Path, default=Path.home() / "Documents/Adressbuch-Sammlung/basel_frueh")
    a = ap.parse_args()
    cfg = json.loads((ROOT / "config/volumes.json").read_text())["volumes"]
    rows, vols = [], []
    for v in cfg:
        if v.get("imported"):  # 1841/1850: Seiten kommen mit scripts/04_import_basel.py
            continue
        vol = v["volume"]
        pdf = a.pdf_dir / v["pdf"]
        doc = pymupdf.open(pdf)
        vols.append({"volume": vol, "pdf": v["pdf"], "pages": len(doc),
                     "sha256": hashlib.sha256(pdf.read_bytes()).hexdigest()})
        for sec in v["sections"]:
            for page in range(sec["from"], sec["to"] + 1):
                read = ROOT / "data/pages" / vol / f"p{page:03d}.jpg"
                web = ROOT / "site/img" / vol / f"p{page:03d}.jpg"
                if not read.exists():
                    read.parent.mkdir(parents=True, exist_ok=True)
                    doc[page - 1].get_pixmap(dpi=150).save(read, jpg_quality=88)
                if not web.exists():
                    web.parent.mkdir(parents=True, exist_ok=True)
                    im = Image.open(read).convert("RGB")
                    im.thumbnail((900, 2000)); im.save(web, quality=60, optimize=True)
                w, h = Image.open(read).size
                rows.append({"volume": vol, "page": page, "section": sec["section"],
                             "image": f"{vol}/p{page:03d}.jpg", "web_image": f"img/{vol}/p{page:03d}.jpg",
                             "width": w, "height": h})
    (ROOT / "data/csv").mkdir(parents=True, exist_ok=True)
    for name, data in (("01_pages.csv", rows), ("00_pdfs.csv", vols)):
        with (ROOT / "data/csv" / name).open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, list(data[0])); w.writeheader(); w.writerows(data)
    print(f"{len(rows)} Seiten in {len(cfg)} Bänden -> data/csv/01_pages.csv")


if __name__ == "__main__":
    main()
