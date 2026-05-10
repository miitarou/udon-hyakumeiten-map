#!/usr/bin/env python3
"""Sync the web app into Capacitor's mobile/www directory."""

from __future__ import annotations

import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MOBILE = ROOT / "mobile"
WWW = MOBILE / "www"
VENDOR = MOBILE / "vendor"

ROOT_FILES = (
    "index.html",
    "style.css",
    "app.js",
    "manifest.webmanifest",
    "icon.svg",
    "privacy.html",
)
DATA_FILES = (
    "data-version.json",
    "udon.json",
    "soba.json",
)


REPLACEMENTS = {
    "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css": "vendor/leaflet/leaflet.css",
    "https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css": "vendor/leaflet.markercluster/MarkerCluster.css",
    "https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css": "vendor/leaflet.markercluster/MarkerCluster.Default.css",
    "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js": "vendor/leaflet/leaflet.js",
    "https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js": "vendor/leaflet.markercluster/leaflet.markercluster.js",
}


def clean_www() -> None:
    if WWW.exists():
        shutil.rmtree(WWW)
    (WWW / "data").mkdir(parents=True)
    (WWW / "vendor").mkdir(parents=True)


def copy_root_files() -> None:
    for name in ROOT_FILES:
        src = ROOT / name
        if not src.exists():
            continue
        dest = WWW / name
        text = src.read_text(encoding="utf-8")
        if name == "index.html":
            text = transform_index(text)
        dest.write_text(text, encoding="utf-8")


def transform_index(text: str) -> str:
    for src, dest in REPLACEMENTS.items():
        text = text.replace(src, dest)
    text = re.sub(r'\n\s*integrity="sha384-[^"]+"\n\s*crossorigin="anonymous"', "", text)
    text = re.sub(r'\n\s*crossorigin="anonymous"', "", text)
    return text


def copy_data_files() -> None:
    for name in DATA_FILES:
        shutil.copy2(ROOT / "data" / name, WWW / "data" / name)


def copy_vendor_files() -> None:
    if not VENDOR.exists():
        raise FileNotFoundError("mobile/vendor is missing. Run the vendor download step first.")
    shutil.copytree(VENDOR, WWW / "vendor", dirs_exist_ok=True)


def main() -> int:
    clean_www()
    copy_root_files()
    copy_data_files()
    copy_vendor_files()
    print(f"Synced web assets to {WWW.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
