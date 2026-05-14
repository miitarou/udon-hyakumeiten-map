#!/usr/bin/env python3
"""Check that changed web assets have matching cache/query version bumps.

This is intentionally lightweight. It catches the common mistake of editing a
served JS/CSS/SW file without changing the cache or query-string version that
forces users' browsers to pick up the new asset.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ZERO_SHA = "0" * 40


WATCHED_FILES = {
    "app.js": "app",
    "style.css": "style",
    "search.js": "search",
    "recommendation-engine.js": "engine",
    "sw.js": "cache",
}


def run_git(args: list[str], *, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        raise SystemExit(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def read_current(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def read_at_ref(ref: str, path: str) -> str | None:
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def extract(pattern: str, text: str, label: str, *, required: bool = True) -> str | None:
    match = re.search(pattern, text)
    if not match:
        if not required:
            return None
        raise SystemExit(f"Could not find {label}")
    return match.group(1)


def versions_from_files(index_html: str, sw_js: str, app_js: str, *, required: bool = True) -> dict[str, str | None]:
    return {
        "app:index": extract(r"app\.js\?v=([0-9.]+)", index_html, "app.js version in index.html", required=required),
        "app:sw": extract(r"app\.js\?v=([0-9.]+)", sw_js, "app.js version in sw.js", required=required),
        "style:index": extract(r"style\.css\?v=([0-9.]+)", index_html, "style.css version in index.html", required=required),
        "style:sw": extract(r"style\.css\?v=([0-9.]+)", sw_js, "style.css version in sw.js", required=required),
        "search:index": extract(r"search\.js\?v=([0-9.]+)", index_html, "search.js version in index.html", required=required),
        "search:sw": extract(r"search\.js\?v=([0-9.]+)", sw_js, "search.js version in sw.js", required=required),
        "engine:app": extract(r"recommendation-engine\.js\?v=([0-9.]+)", app_js, "recommendation-engine.js version in app.js", required=required),
        "engine:sw": extract(r"recommendation-engine\.js\?v=([0-9.]+)", sw_js, "recommendation-engine.js version in sw.js", required=required),
        "cache": extract(r"hyakumeiten-map-v(\d+)", sw_js, "Service Worker cache version", required=required),
    }


def print_current_versions() -> None:
    versions = versions_from_files(
        read_current("index.html"),
        read_current("sw.js"),
        read_current("app.js"),
    )
    print("Web version summary")
    for key, value in versions.items():
        print(f"- {key}: {value}")


def changed_files(base: str) -> set[str]:
    output = run_git(["diff", "--name-only", f"{base}...HEAD"])
    return {line.strip() for line in output.splitlines() if line.strip()}


def compare_versions(base: str, changed: set[str]) -> list[str]:
    old_index = read_at_ref(base, "index.html")
    old_sw = read_at_ref(base, "sw.js")
    old_app = read_at_ref(base, "app.js")
    if old_index is None or old_sw is None or old_app is None:
        return [f"Cannot read version-bearing files at base ref {base}; skipping strict version check."]

    required = {WATCHED_FILES[path] for path in changed if path in WATCHED_FILES}
    if not required:
        return []

    old_versions = versions_from_files(old_index, old_sw, old_app, required=False)
    new_versions = versions_from_files(
        read_current("index.html"),
        read_current("sw.js"),
        read_current("app.js"),
    )

    warnings: list[str] = []

    if "app" in required:
        if old_versions["app:index"] == new_versions["app:index"]:
            warnings.append("app.js changed but index.html app.js?v was not bumped.")
        if old_versions["app:sw"] == new_versions["app:sw"]:
            warnings.append("app.js changed but sw.js app.js?v was not bumped.")
    if "style" in required:
        if old_versions["style:index"] == new_versions["style:index"]:
            warnings.append("style.css changed but index.html style.css?v was not bumped.")
        if old_versions["style:sw"] == new_versions["style:sw"]:
            warnings.append("style.css changed but sw.js style.css?v was not bumped.")
    if "search" in required:
        if old_versions["search:index"] == new_versions["search:index"]:
            warnings.append("search.js changed but index.html search.js?v was not bumped.")
        if old_versions["search:sw"] == new_versions["search:sw"]:
            warnings.append("search.js changed but sw.js search.js?v was not bumped.")
    if "engine" in required:
        if old_versions["engine:app"] == new_versions["engine:app"]:
            warnings.append("recommendation-engine.js changed but app.js import version was not bumped.")
        if old_versions["engine:sw"] == new_versions["engine:sw"]:
            warnings.append("recommendation-engine.js changed but sw.js cache version for it was not bumped.")
    if required and old_versions["cache"] == new_versions["cache"]:
        warnings.append("served asset changed but Service Worker CACHE_NAME was not bumped.")

    return warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Check web asset version bumps.")
    parser.add_argument("--base", help="Base git ref to compare with HEAD. If omitted, only prints current versions.")
    args = parser.parse_args()

    print_current_versions()
    base = args.base
    if not base or base == ZERO_SHA:
        print("No usable base ref supplied; strict diff check skipped.")
        return 0

    if subprocess.run(["git", "rev-parse", "--verify", base], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0:
        print(f"Base ref {base} is unavailable; strict diff check skipped.")
        return 0

    changed = changed_files(base)
    relevant = sorted(path for path in changed if path in WATCHED_FILES)
    print(f"Changed watched assets: {', '.join(relevant) if relevant else 'none'}")
    warnings = compare_versions(base, changed)
    if warnings:
        print("Version bump check FAILED")
        for warning in warnings:
            print(f"- {warning}")
        return 1
    print("Version bump check PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
