#!/usr/bin/env python3
"""Generate the external-signal review backlog.

The backlog is a deterministic work queue for expanding
data/external_source_registry.json.  It does not claim that any external source
has been reviewed.  Rows move from this backlog to the registry only after a
short evidence-term review is completed.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASETS = (ROOT / "data" / "udon.json", ROOT / "data" / "soba.json")
REGISTRY = ROOT / "data" / "external_source_registry.json"
REVIEW_LOG = ROOT / "data" / "external_source_review_log.json"
OUTPUT = ROOT / "data" / "external_signal_backlog.json"
HALL_OF_FAME_THRESHOLDS = {
    "udon": 6,
    "soba": 4,
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def priority_tier(restaurant: dict[str, Any]) -> str:
    category = restaurant.get("category")
    selection_count = len(restaurant.get("years") or [])
    if selection_count >= HALL_OF_FAME_THRESHOLDS.get(category, 999):
        return "hall_of_fame_remaining"
    if selection_count >= 4:
        return "high_selection_remaining"
    if selection_count >= 2:
        return "repeat_selection_remaining"
    if restaurant.get("firstSelected"):
        return "latest_new_remaining"
    return "single_selection_remaining"


def priority_rank(row: dict[str, Any]) -> tuple[int, int, str, str, str, str]:
    tier_order = {
        "hall_of_fame_remaining": 0,
        "high_selection_remaining": 1,
        "repeat_selection_remaining": 2,
        "latest_new_remaining": 3,
        "single_selection_remaining": 4,
    }
    return (
        tier_order.get(row["priorityTier"], 99),
        -int(row["selectionCount"]),
        row["category"],
        row["region"],
        row["prefecture"],
        row["name"],
    )


def generate_payload() -> dict[str, Any]:
    restaurants: list[dict[str, Any]] = []
    for path in DATASETS:
        rows = load_json(path)
        if not isinstance(rows, list):
            raise ValueError(f"{path.relative_to(ROOT)} must be a list")
        restaurants.extend(rows)

    registry = load_json(REGISTRY)
    covered_urls = {
        row["restaurantUrl"]
        for row in registry.get("sources", [])
        if isinstance(row, dict) and isinstance(row.get("restaurantUrl"), str)
    }
    try:
        review_log = load_json(REVIEW_LOG)
    except FileNotFoundError:
        review_log = {"reviews": []}
    reviewed_urls = {
        row["restaurantUrl"]
        for row in review_log.get("reviews", [])
        if isinstance(row, dict) and isinstance(row.get("restaurantUrl"), str)
    }
    completed_urls = covered_urls | reviewed_urls

    backlog: list[dict[str, Any]] = []
    for restaurant in restaurants:
        url = restaurant.get("url")
        if not isinstance(url, str) or url in completed_urls:
            continue
        years = sorted(restaurant.get("years") or [])
        row = {
            "url": url,
            "name": restaurant.get("name"),
            "category": restaurant.get("category"),
            "prefecture": restaurant.get("prefecture"),
            "region": restaurant.get("region"),
            "area": restaurant.get("area") or "",
            "selectionCount": len(years),
            "years": years,
            "closed": bool(restaurant.get("closed")),
            "priorityTier": priority_tier(restaurant),
            "status": "pending_source_review",
            "nextAction": "Find one allowed source and register short evidenceTerms in data/external_source_registry.json.",
        }
        backlog.append(row)

    backlog.sort(key=priority_rank)
    summary = {
        "totalRestaurants": len(restaurants),
        "coveredRestaurants": len(covered_urls),
        "reviewedRestaurants": len(reviewed_urls),
        "completedRestaurants": len(completed_urls),
        "remainingRestaurants": len(backlog),
        "remainingByCategory": dict(Counter(row["category"] for row in backlog)),
        "remainingByPriorityTier": dict(Counter(row["priorityTier"] for row in backlog)),
    }
    reviewed_dates = [
        row.get("lastCheckedAt")
        for row in registry.get("sources", [])
        if isinstance(row, dict) and isinstance(row.get("lastCheckedAt"), str)
    ]

    return {
        "version": 1,
        "generatedAt": max(reviewed_dates, default=date.today().isoformat()),
        "policy": {
            "summary": "Work queue for expanding external recommendation signals. Rows are not used by the app until manually reviewed and moved into external_source_registry.json.",
            "allowedSources": ["official_site", "official_tourism", "public_directory", "manual_editorial_seed"],
            "disallowedStorage": ["raw page text", "review bodies", "ratings", "photos", "SNS posts", "user names"],
        },
        "hallOfFameThresholds": HALL_OF_FAME_THRESHOLDS,
        "summary": summary,
        "restaurants": backlog,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate external-signal review backlog.")
    parser.add_argument("--check", action="store_true", help="Exit non-zero if data/external_signal_backlog.json is stale.")
    args = parser.parse_args()

    payload = generate_payload()
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"

    if args.check:
        try:
            current = OUTPUT.read_text(encoding="utf-8")
        except FileNotFoundError:
            print(f"{OUTPUT.relative_to(ROOT)} does not exist", file=sys.stderr)
            return 1
        if current != text:
            print(f"{OUTPUT.relative_to(ROOT)} is stale. Run scripts/generate_external_signal_backlog.py", file=sys.stderr)
            return 1
        print(f"{OUTPUT.relative_to(ROOT)} is up to date.")
        return 0

    OUTPUT.write_text(text, encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    print(
        f"covered={payload['summary']['coveredRestaurants']} "
        f"remaining={payload['summary']['remainingRestaurants']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
