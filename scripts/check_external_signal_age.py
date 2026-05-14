#!/usr/bin/env python3
"""Report stale external source reviews.

The external signal registry is a manually reviewed source ledger. This script
does not fail CI; it only surfaces rows that may need rechecking.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "external_source_registry.json"
WARN_DAYS = 180
STRONG_WARN_DAYS = 365


def parse_date(value: object) -> date | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def main() -> int:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    today = date.today()
    stale = []
    missing = []

    for row in payload.get("sources", []):
        checked_at = parse_date(row.get("lastCheckedAt"))
        if not checked_at:
            missing.append(row)
            continue
        age_days = (today - checked_at).days
        if age_days > WARN_DAYS:
            stale.append((age_days, row))

    stale.sort(reverse=True, key=lambda item: item[0])
    strong = [item for item in stale if item[0] > STRONG_WARN_DAYS]

    print("External signal freshness report (report-only)")
    print(f"- sources: {len(payload.get('sources', []))}")
    print(f"- missing lastCheckedAt: {len(missing)}")
    print(f"- older than {WARN_DAYS} days: {len(stale)}")
    print(f"- older than {STRONG_WARN_DAYS} days: {len(strong)}")

    for age_days, row in stale[:10]:
        print(f"  WARN {age_days}d {row.get('name', '(unknown)')} - {row.get('sourceTitle', row.get('sourceUrl', ''))}")
    for row in missing[:10]:
        print(f"  WARN missing date {row.get('name', '(unknown)')} - {row.get('sourceTitle', row.get('sourceUrl', ''))}")

    if stale or missing:
        print("Report-only warnings found. This check does not fail CI.")
    else:
        print("All reviewed external signal sources are fresh enough.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
