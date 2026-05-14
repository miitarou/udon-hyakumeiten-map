#!/usr/bin/env python3
"""Bump the lightweight web asset/cache versions.

This project intentionally avoids a frontend build step. This helper keeps the
manual query-string versions and Service Worker cache name aligned.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def next_decimal_version(value: str) -> str:
    parts = value.split(".")
    if len(parts) == 1:
        return str(int(parts[0]) + 1)
    parts[-1] = str(int(parts[-1]) + 1)
    return ".".join(parts)


def current_asset_version(index_html: str) -> str:
    match = re.search(r"app\.js\?v=([0-9.]+)", index_html)
    if not match:
        raise SystemExit("Could not find app.js?v=... in index.html")
    return match.group(1)


def current_cache_version(sw_js: str) -> int:
    match = re.search(r"hyakumeiten-map-v(\d+)", sw_js)
    if not match:
        raise SystemExit("Could not find hyakumeiten-map-vN in sw.js")
    return int(match.group(1))


def replace_asset_versions(text: str, asset_version: str) -> str:
    text = re.sub(r"style\.css\?v=[0-9.]+", f"style.css?v={asset_version}", text)
    text = re.sub(r"app\.js\?v=[0-9.]+", f"app.js?v={asset_version}", text)
    return text


def replace_search_version(text: str, search_version: str | None) -> str:
    if search_version is None:
        return text
    return re.sub(r"search\.js\?v=[0-9.]+", f"search.js?v={search_version}", text)


def replace_engine_version(text: str, engine_version: str | None) -> str:
    if engine_version is None:
        return text
    return re.sub(
        r"recommendation-engine\.js\?v=[0-9.]+",
        f"recommendation-engine.js?v={engine_version}",
        text,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Bump web asset versions without a build step.")
    parser.add_argument("--asset-version", help="Version for app.js/style.css query strings. Defaults to current patch + 1.")
    parser.add_argument("--cache-version", type=int, help="Service Worker cache number. Defaults to current + 1.")
    parser.add_argument("--search-version", help="Optional version for search.js query strings.")
    parser.add_argument("--engine-version", help="Optional version for recommendation-engine.js query strings.")
    parser.add_argument("--check", action="store_true", help="Report current versions without modifying files.")
    args = parser.parse_args()

    index_path = ROOT / "index.html"
    sw_path = ROOT / "sw.js"
    app_path = ROOT / "app.js"
    update_guide_path = ROOT / "docs" / "update-guide.md"

    index_html = read(index_path)
    sw_js = read(sw_path)
    app_js = read(app_path)
    update_guide = read(update_guide_path)

    current_asset = current_asset_version(index_html)
    current_cache = current_cache_version(sw_js)
    asset_version = args.asset_version or next_decimal_version(current_asset)
    cache_version = args.cache_version if args.cache_version is not None else current_cache + 1

    if args.check:
        print(f"asset-version: {current_asset}")
        print(f"cache-version: {current_cache}")
        return 0

    index_html = replace_asset_versions(index_html, asset_version)
    sw_js = replace_asset_versions(sw_js, asset_version)
    sw_js = re.sub(r"hyakumeiten-map-v\d+", f"hyakumeiten-map-v{cache_version}", sw_js)
    update_guide = replace_asset_versions(update_guide, asset_version)
    update_guide = re.sub(r"hyakumeiten-map-v\d+", f"hyakumeiten-map-v{cache_version}", update_guide)

    index_html = replace_search_version(index_html, args.search_version)
    sw_js = replace_search_version(sw_js, args.search_version)
    update_guide = replace_search_version(update_guide, args.search_version)

    index_html = replace_engine_version(index_html, args.engine_version)
    sw_js = replace_engine_version(sw_js, args.engine_version)
    app_js = replace_engine_version(app_js, args.engine_version)
    update_guide = replace_engine_version(update_guide, args.engine_version)

    write(index_path, index_html)
    write(sw_path, sw_js)
    write(app_path, app_js)
    write(update_guide_path, update_guide)

    print(f"Bumped app/style asset version to {asset_version}")
    print(f"Bumped Service Worker cache to hyakumeiten-map-v{cache_version}")
    if args.search_version:
        print(f"Set search.js version to {args.search_version}")
    if args.engine_version:
        print(f"Set recommendation-engine.js version to {args.engine_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
