#!/usr/bin/env python3
"""Validate public restaurant JSON data.

This script intentionally uses only the Python standard library so it can run
in GitHub Actions without dependency setup.
"""

from __future__ import annotations

import json
import re
import hashlib
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
DATA_VERSION = "data/data-version.json"
RECOMMENDATION_TAGS = "data/recommendation_tags.json"
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
VALID_TAG_SOURCES = {"data", "name_keyword", "selection_prior", "regional_prior", "model_prior"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def validate_data_version(dataset_records: dict[str, int]) -> tuple[int, int]:
    path = ROOT / DATA_VERSION
    print(f"Checking {DATA_VERSION}...")
    try:
        version = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"  [ERROR] Failed to load {DATA_VERSION}: {exc}")
        return 1, 0

    errors: list[str] = []
    warnings: list[str] = []
    datasets = version.get("datasets")
    if version.get("version") != 1:
        errors.append("version must be 1")
    if not isinstance(version.get("generatedAt"), str) or not version["generatedAt"]:
        errors.append("generatedAt must be a non-empty string")
    if not isinstance(datasets, dict):
        errors.append("datasets must be an object")
        datasets = {}

    for relative_path, expected_category in DATASETS:
        key = expected_category
        item = datasets.get(key)
        if not isinstance(item, dict):
            errors.append(f"datasets.{key} must be an object")
            continue
        if item.get("path") != relative_path:
            errors.append(f"datasets.{key}.path must be {relative_path!r}")
        if item.get("records") != dataset_records.get(relative_path):
            errors.append(f"datasets.{key}.records is stale: {item.get('records')!r}")
        actual_sha = sha256(ROOT / relative_path)
        if item.get("sha256") != actual_sha:
            errors.append(f"datasets.{key}.sha256 is stale")

    for error in errors:
        print(f"  [ERROR] {error}")
    for warning in warnings:
        print(f"  [WARN] {warning}")
    print(f"  Summary: errors={len(errors)}, warnings={len(warnings)}")
    return len(errors), len(warnings)


def validate_recommendation_tags(known_restaurants: dict[str, dict]) -> tuple[int, int]:
    path = ROOT / RECOMMENDATION_TAGS
    print(f"Checking {RECOMMENDATION_TAGS}...")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"  [WARN] {RECOMMENDATION_TAGS} does not exist")
        return 0, 1
    except Exception as exc:  # noqa: BLE001
        print(f"  [ERROR] Failed to load {RECOMMENDATION_TAGS}: {exc}")
        return 1, 0

    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(payload, dict):
        errors.append("root must be an object")
        payload = {}

    if payload.get("version") != 1:
        errors.append("version must be 1")

    tag_definitions = payload.get("tagDefinitions")
    if not isinstance(tag_definitions, dict) or not tag_definitions:
        errors.append("tagDefinitions must be a non-empty object")
        tag_definitions = {}

    restaurants = payload.get("restaurants")
    if not isinstance(restaurants, list):
        errors.append("restaurants must be a list")
        restaurants = []

    seen_urls: set[str] = set()
    for index, item in enumerate(restaurants):
        prefix = f"item {index}"
        if not isinstance(item, dict):
            errors.append(f"{prefix}: must be an object")
            continue

        url = item.get("url")
        if not isinstance(url, str) or not url:
            errors.append(f"{prefix}: url must be a non-empty string")
            continue
        if url in seen_urls:
            errors.append(f"{prefix}: duplicate url {url}")
        seen_urls.add(url)

        known = known_restaurants.get(url)
        if not known:
            errors.append(f"{prefix}: url is not present in public restaurant data: {url}")
        else:
            if item.get("name") != known.get("name"):
                errors.append(f"{prefix}: name mismatch for {url}")
            if item.get("category") != known.get("category"):
                errors.append(f"{prefix}: category mismatch for {url}")

        tags = item.get("tags")
        if not isinstance(tags, list) or not tags:
            errors.append(f"{prefix}: tags must be a non-empty list")
            continue

        seen_tag_keys: set[str] = set()
        for tag_index, tag in enumerate(tags):
            tag_prefix = f"{prefix}.tags[{tag_index}]"
            if not isinstance(tag, dict):
                errors.append(f"{tag_prefix}: must be an object")
                continue
            key = tag.get("key")
            if not isinstance(key, str) or not key:
                errors.append(f"{tag_prefix}: key must be a non-empty string")
                continue
            if key in seen_tag_keys:
                errors.append(f"{tag_prefix}: duplicate tag key {key}")
            seen_tag_keys.add(key)
            if key not in tag_definitions:
                errors.append(f"{tag_prefix}: missing tag definition for {key}")

            for field in ("weight", "confidence"):
                value = tag.get(field)
                if not isinstance(value, (int, float)) or isinstance(value, bool) or not (0 <= float(value) <= 1):
                    errors.append(f"{tag_prefix}: {field} must be a number between 0 and 1")

            source = tag.get("source")
            if source not in VALID_TAG_SOURCES:
                errors.append(f"{tag_prefix}: source must be one of {sorted(VALID_TAG_SOURCES)}, got {source!r}")

            evidence = tag.get("evidence")
            if not isinstance(evidence, list) or not evidence or not all(isinstance(value, str) and value for value in evidence):
                errors.append(f"{tag_prefix}: evidence must be a non-empty list of strings")

    expected_urls = set(known_restaurants)
    if seen_urls != expected_urls:
        missing = sorted(expected_urls - seen_urls)
        extra = sorted(seen_urls - expected_urls)
        if missing:
            errors.append(f"missing recommendation records: {len(missing)}")
        if extra:
            errors.append(f"extra recommendation records: {len(extra)}")

    for key, definition in tag_definitions.items():
        if not isinstance(definition, dict):
            errors.append(f"tagDefinitions.{key}: must be an object")
            continue
        if definition.get("kind") not in {"fact", "inferred"}:
            errors.append(f"tagDefinitions.{key}.kind must be fact or inferred")
        if not isinstance(definition.get("label"), str) or not definition["label"]:
            errors.append(f"tagDefinitions.{key}.label must be a non-empty string")

    for error in errors:
        print(f"  [ERROR] {error}")
    for warning in warnings:
        print(f"  [WARN] {warning}")
    print(f"  Summary: records={len(restaurants)}, errors={len(errors)}, warnings={len(warnings)}")
    return len(errors), len(warnings)


def main() -> int:
    total_records = 0
    total_errors = 0
    total_warnings = 0
    dataset_records: dict[str, int] = {}
    known_restaurants: dict[str, dict] = {}

    for relative_path, expected_category in DATASETS:
        records, errors, warnings = validate_dataset(relative_path, expected_category)
        dataset_records[relative_path] = records
        total_records += records
        total_errors += errors
        total_warnings += warnings
        data, load_errors = load_json(ROOT / relative_path)
        if not load_errors:
            for item in data:
                if isinstance(item, dict) and isinstance(item.get("url"), str):
                    known_restaurants[item["url"]] = item

    version_errors, version_warnings = validate_data_version(dataset_records)
    total_errors += version_errors
    total_warnings += version_warnings

    tag_errors, tag_warnings = validate_recommendation_tags(known_restaurants)
    total_errors += tag_errors
    total_warnings += tag_warnings

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
