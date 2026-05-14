#!/usr/bin/env python3
"""Report repository asset sizes against soft budgets.

This check is intentionally report-only. It helps notice frontend/data growth
without blocking routine data updates.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SOFT_BUDGETS = {
    "app.js": 160 * 1024,
    "style.css": 80 * 1024,
    "recommendation-engine.js": 50 * 1024,
    "data/recommendation_tags.json": 2800 * 1024,
    "data/external_signals.json": 1400 * 1024,
}


def human_size(size: int) -> str:
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.2f} MB"
    if size >= 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size} B"


def main() -> int:
    print("Asset size budget report (report-only)")
    warnings = 0
    for rel_path, budget in SOFT_BUDGETS.items():
        path = ROOT / rel_path
        if not path.exists():
            print(f"- WARN {rel_path}: missing")
            warnings += 1
            continue
        size = path.stat().st_size
        status = "OK" if size <= budget else "WARN"
        if status == "WARN":
            warnings += 1
        print(f"- {status} {rel_path}: {human_size(size)} / soft budget {human_size(budget)}")

    if warnings:
        print(f"Report-only warnings: {warnings}. This check does not fail CI.")
    else:
        print("All tracked assets are within soft budgets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
