#!/usr/bin/env python3
"""Validate public restaurant JSON data.

This script intentionally uses only the Python standard library so it can run
in GitHub Actions without dependency setup.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DATASETS = (
    ("data/udon.json", "udon"),
    ("data/soba.json", "soba"),
)
REQUIRED_FIELDS = ("name", "category", "prefecture", "region", "lat", "lng", "url", "years")
RECOMMENDED_FIELDS = ("area", "address", "closed", "firstSelected")
VALID_CATEGORIES = {"udon", "soba"}
VALID_REGIONS = {
    "udon": {"EAST", "WEST", "KAGAWA"},
    "soba": {"EAST", "WEST"},
}
ALLOWED_URL_HOSTS = {"tabelog.com"}
TEXT_FIELDS = ("name", "prefecture", "region", "area", "address")
MIN_YEAR = 2017
MAX_YEAR = 2026
MIN_LAT, MAX_LAT = 20.0, 46.5
MIN_LNG, MAX_LNG = 122.0, 154.0
HTML_TAG_RE = re.compile(r"<[^>]+>")


def normalize(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).strip().lower()
    return re.sub(r"\s+", "", text)


def load_json(path: Path) -> tuple[list[dict], list[str]]:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:  # noqa: BLE001 - validation script should report all load failures plainly
        return [], [f"Failed to load {path}: {exc}"]

    if not isinstance(data, list):
        return [], [f"Root JSON should be a list: {path}"]

    return data, []


def validate_item(item: object, index: int, expected_category: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(item, dict):
        return [f"Item {index} is not an object"], warnings

    name = item.get("name", f"item {index}")

    for field in REQUIRED_FIELDS:
        if field not in item:
            errors.append(f"{name}: missing required field '{field}'")

    for field in RECOMMENDED_FIELDS:
        if field not in item or item.get(field) in (None, ""):
            warnings.append(f"{name}: missing recommended field '{field}'")

    category = item.get("category")
    if category is not None and category not in VALID_CATEGORIES:
        errors.append(f"{name}: category must be one of {sorted(VALID_CATEGORIES)}, got {category!r}")
    if category is not None and category != expected_category:
        errors.append(f"{name}: category mismatch, expected {expected_category!r}, got {category!r}")

    region = item.get("region")
    if category in VALID_REGIONS and region not in VALID_REGIONS[category]:
        errors.append(f"{name}: region {region!r} is not valid for category {category!r}")

    lat = item.get("lat")
    lng = item.get("lng")
    if not isinstance(lat, (int, float)) or isinstance(lat, bool):
        errors.append(f"{name}: lat must be numeric")
    elif not (MIN_LAT <= float(lat) <= MAX_LAT):
        errors.append(f"{name}: lat out of Japan-ish bounds: {lat}")

    if not isinstance(lng, (int, float)) or isinstance(lng, bool):
        errors.append(f"{name}: lng must be numeric")
    elif not (MIN_LNG <= float(lng) <= MAX_LNG):
        errors.append(f"{name}: lng out of Japan-ish bounds: {lng}")

    years = item.get("years")
    if not isinstance(years, list) or not years:
        errors.append(f"{name}: years must be a non-empty list")
    else:
        invalid_years = [y for y in years if not isinstance(y, int) or isinstance(y, bool) or not (MIN_YEAR <= y <= MAX_YEAR)]
        if invalid_years:
            errors.append(f"{name}: years must be integers between {MIN_YEAR} and {MAX_YEAR}: {invalid_years}")

    url = item.get("url")
    if url and not (isinstance(url, str) and (url.startswith("http://") or url.startswith("https://"))):
        errors.append(f"{name}: url must start with http:// or https://")
    elif url:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        if parsed.scheme != "https":
            errors.append(f"{name}: url must use https")
        if not any(hostname == host or hostname.endswith(f".{host}") for host in ALLOWED_URL_HOSTS):
            errors.append(f"{name}: url host is not allowed: {hostname}")

    for field in TEXT_FIELDS:
        value = item.get(field)
        if isinstance(value, str) and HTML_TAG_RE.search(value):
            errors.append(f"{name}: field '{field}' appears to contain HTML")

    for field in ("closed", "firstSelected"):
        value = item.get(field)
        if value is not None and not isinstance(value, bool):
            errors.append(f"{name}: {field} must be boolean")

    return errors, warnings


def validate_dataset(relative_path: str, expected_category: str) -> tuple[int, int, int]:
    path = ROOT / relative_path
    print(f"Checking {relative_path}...")

    data, load_errors = load_json(path)
    if load_errors:
        for error in load_errors:
            print(f"  [ERROR] {error}")
        return 0, len(load_errors), 0

    errors: list[str] = []
    warnings: list[str] = []
    duplicate_candidates: dict[str, list[str]] = defaultdict(list)

    for index, item in enumerate(data):
        item_errors, item_warnings = validate_item(item, index, expected_category)
        errors.extend(f"item {index}: {message}" for message in item_errors)
        warnings.extend(f"item {index}: {message}" for message in item_warnings)

        if isinstance(item, dict):
            key = f"{normalize(item.get('name'))}|{normalize(item.get('prefecture'))}"
            if key != "|":
                duplicate_candidates[key].append(str(item.get("url") or item.get("address") or index))

    for key, values in duplicate_candidates.items():
        if len(values) > 1:
            warnings.append(f"duplicate candidate {key}: {', '.join(values)}")

    for error in errors:
        print(f"  [ERROR] {error}")
    for warning in warnings:
        print(f"  [WARN] {warning}")

    duplicate_count = sum(1 for values in duplicate_candidates.values() if len(values) > 1)
    print(
        f"  Summary: records={len(data)}, errors={len(errors)}, "
        f"warnings={len(warnings)}, duplicate_candidates={duplicate_count}"
    )
    return len(data), len(errors), len(warnings)


def main() -> int:
    total_records = 0
    total_errors = 0
    total_warnings = 0

    for relative_path, expected_category in DATASETS:
        records, errors, warnings = validate_dataset(relative_path, expected_category)
        total_records += records
        total_errors += errors
        total_warnings += warnings

    print("\nFinal summary")
    print(f"  total_records={total_records}")
    print(f"  total_errors={total_errors}")
    print(f"  total_warnings={total_warnings}")

    if total_errors:
        print("Data validation FAILED.")
        return 1

    print("Data validation PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
