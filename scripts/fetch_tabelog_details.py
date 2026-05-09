"""
Fetch restaurant addresses and coordinates from Tabelog store pages.

This script fixes map-coordinate drift caused by area/station geocoding.
It updates both display JSON files and their raw counterparts:

  - data/soba.json
  - data/soba_raw.json
  - data/udon.json
  - data/udon_raw.json

Usage:
  cd <repo-root>
  python3 scripts/fetch_tabelog_details.py
"""

from __future__ import annotations

import concurrent.futures
import html
import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

# Some old 2017 entries only had a store id and a prefecture slug.
# Tabelog needs the area path for these pages.
URL_OVERRIDES_BY_ID = {
    "14000035": "https://tabelog.com/kanagawa/A1405/A140507/14000035/",
    "37000383": "https://tabelog.com/kagawa/A3701/A370101/37000383/",
    "27007177": "https://tabelog.com/osaka/A2707/A270701/27007177/",
    "27004475": "https://tabelog.com/osaka/A2701/A270101/27004475/",
    "27001207": "https://tabelog.com/osaka/A2701/A270202/27001207/",
    "40033482": "https://tabelog.com/fukuoka/A4001/A400101/40033482/",
}


@dataclass
class Details:
    url: str
    canonical_url: str | None
    lat: float | None
    lng: float | None
    address: str | None
    closed: bool | None
    error: str | None = None


def extract_store_id(url: str) -> str | None:
    match = re.search(r"/(\d+)(?:/|$)", url)
    return match.group(1) if match else None


def request_html(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "ja,en;q=0.5",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def clean_text(value: str) -> str:
    value = re.sub(r"<.*?>", "", value, flags=re.S)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def parse_details(url: str, body: str) -> Details:
    lat = lng = None
    lat_match = re.search(r'"latitude"\s*:\s*([0-9.]+)', body)
    lng_match = re.search(r'"longitude"\s*:\s*([0-9.]+)', body)
    if lat_match and lng_match:
        lat = float(lat_match.group(1))
        lng = float(lng_match.group(1))

    address = None
    address_patterns = [
        r'<p class="rstinfo-table__address">(.*?)</p>',
        r'"address"\s*:\s*"([^"]+)"',
    ]
    for pattern in address_patterns:
        match = re.search(pattern, body, flags=re.S)
        if match:
            address = clean_text(match.group(1))
            break

    canonical_url = None
    canonical_patterns = [
        r'<meta property="og:url" content="([^"]+)"',
        r'<link rel="canonical" href="([^"]+)"',
    ]
    for pattern in canonical_patterns:
        match = re.search(pattern, body)
        if match:
            canonical_url = html.unescape(match.group(1)).split("?")[0]
            if canonical_url.endswith("/dtlphotolst/smp2/"):
                canonical_url = canonical_url.replace("/dtlphotolst/smp2/", "/")
            break

    closed = None
    if "このお店は現在閉店しております" in body or "移転前の店舗情報です" in body:
        closed = True
    elif lat is not None and lng is not None:
        closed = False

    return Details(url, canonical_url, lat, lng, address, closed)


def fetch_details(url: str) -> Details:
    store_id = extract_store_id(url)
    candidates = [url]
    if store_id and store_id in URL_OVERRIDES_BY_ID:
        override = URL_OVERRIDES_BY_ID[store_id]
        if override not in candidates:
            candidates.insert(0, override)

    last_error = None
    for candidate in candidates:
        try:
            body = request_html(candidate)
            return parse_details(candidate, body)
        except urllib.error.HTTPError as exc:
            last_error = f"HTTP {exc.code}"
        except Exception as exc:  # noqa: BLE001 - CLI report should keep going.
            last_error = repr(exc)
        time.sleep(0.2)

    return Details(url, None, None, None, None, None, last_error)


def collect_urls(paths: list[Path]) -> list[str]:
    urls: set[str] = set()
    for path in paths:
        with open(path, encoding="utf-8") as f:
            for row in json.load(f):
                if row.get("url"):
                    urls.add(row["url"])
    return sorted(urls)


def apply_details(path: Path, details_by_id: dict[str, Details]) -> tuple[int, int, int]:
    with open(path, encoding="utf-8") as f:
        rows: list[dict[str, Any]] = json.load(f)

    changed = missing = closed_count = 0
    for row in rows:
        store_id = extract_store_id(row.get("url", ""))
        details = details_by_id.get(store_id or "")
        if not details or details.lat is None or details.lng is None:
            missing += 1
            continue

        before = json.dumps(row, ensure_ascii=False, sort_keys=True)
        row["lat"] = details.lat
        row["lng"] = details.lng
        if details.address:
            row["address"] = details.address
        if details.canonical_url:
            row["url"] = details.canonical_url.rstrip("/") + "/"
        if details.closed is not None:
            row["closed"] = details.closed
        if row.get("closed"):
            closed_count += 1

        after = json.dumps(row, ensure_ascii=False, sort_keys=True)
        if after != before:
            changed += 1

    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
        f.write("\n")

    return changed, missing, closed_count


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    paths = [
        base_dir / "data" / "soba.json",
        base_dir / "data" / "soba_raw.json",
        base_dir / "data" / "udon.json",
        base_dir / "data" / "udon_raw.json",
    ]

    urls = collect_urls(paths)
    print(f"Fetching Tabelog details for {len(urls)} unique URLs...")

    details_by_id: dict[str, Details] = {}
    failures: list[Details] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        for i, details in enumerate(executor.map(fetch_details, urls), 1):
            store_id = extract_store_id(details.canonical_url or details.url)
            if store_id:
                details_by_id[store_id] = details
            if details.lat is None or details.lng is None:
                failures.append(details)
            if i % 50 == 0:
                print(f"  fetched {i}/{len(urls)}")

    print(f"Fetched coordinates: {len(details_by_id) - len(failures)}")
    if failures:
        print(f"Coordinate failures: {len(failures)}")
        for failure in failures[:20]:
            print(f"  - {failure.url}: {failure.error}")

    for path in paths:
        changed, missing, closed_count = apply_details(path, details_by_id)
        print(
            f"Updated {path.relative_to(base_dir)}: "
            f"changed={changed}, missing_details={missing}, closed={closed_count}"
        )


if __name__ == "__main__":
    main()
