#!/usr/bin/env python3
"""Report recommendation results for the golden-set review cases.

This is intentionally a report-only evaluator. It mirrors the browser-side
recommendation scoring closely enough to review ranking drift without turning
subjective taste judgments into CI failures.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASETS = (ROOT / "data" / "udon.json", ROOT / "data" / "soba.json")
RECOMMENDATION_TAGS = ROOT / "data" / "recommendation_tags.json"
GOLDEN_SET = ROOT / "data" / "recommendation_golden_set.json"

INITIAL_LIMIT = 3
MAX_LIMIT = 9
PREFIX_WEIGHTS = {
    "genre": 0.9,
    "style": 1.45,
    "texture": 1.45,
    "dish": 1.35,
    "lineage": 1.3,
    "scene": 1.08,
    "mood": 1.15,
    "pref": 0.42,
    "macro_area": 0.32,
    "selection": 0.34,
    "region": 0.25,
    "status": 0,
}
REASON_PRIORITY = {
    "style": 1.6,
    "texture": 1.55,
    "dish": 1.5,
    "lineage": 1.4,
    "scene": 1.15,
    "mood": 1.1,
    "genre": 0,
    "selection": 0.55,
    "pref": 0,
    "macro_area": 0,
    "region": 0,
    "status": 0,
}
PRIMARY_REASON_PREFIXES = {"style", "texture", "dish", "mood", "scene", "lineage"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_restaurants() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in DATASETS:
        rows.extend(load_json(path))
    return rows


def tag_prefix(key: str) -> str:
    return str(key or "").split(".")[0]


def mode_factor(prefix: str, mode: str) -> float:
    if mode == "nearby":
        if prefix in {"pref", "macro_area"}:
            return 1.12
        if prefix == "region":
            return 0.85
        if prefix == "genre":
            return 0.82
        if prefix in {"style", "texture", "dish"}:
            return 1.04
    if mode == "expand":
        if prefix == "genre":
            return 0.58
        if prefix == "pref":
            return 0.22
        if prefix in {"macro_area", "region"}:
            return 0.58
        if prefix in {"style", "texture", "dish", "lineage"}:
            return 1.22
        if prefix in {"scene", "mood"}:
            return 1.12
    return 1.0


def tag_weight(key: str, mode: str) -> float:
    prefix = tag_prefix(key)
    base = PREFIX_WEIGHTS.get(prefix, 0.6)
    return 0 if base <= 0 else base * mode_factor(prefix, mode)


def tag_map(record: dict[str, Any]) -> dict[str, float]:
    result: dict[str, float] = {}
    for tag in record.get("tags") or []:
        key = str(tag.get("key") or "")
        if not key or tag_prefix(key) == "status":
            continue
        try:
            weight = float(tag.get("weight"))
            confidence = float(tag.get("confidence"))
        except (TypeError, ValueError):
            continue
        result[key] = max(0.0, weight) * max(0.0, confidence)
    return result


def distance_km(a: dict[str, Any], b: dict[str, Any]) -> float:
    if a.get("lat") is None or a.get("lng") is None or b.get("lat") is None or b.get("lng") is None:
        return math.inf
    radius = 6371.0
    lat1 = math.radians(float(a["lat"]))
    lat2 = math.radians(float(b["lat"]))
    dlat = lat2 - lat1
    dlng = math.radians(float(b["lng"]) - float(a["lng"]))
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(h), math.sqrt(1 - h))


def map_similarity(a_tags: dict[str, float], b_tags: dict[str, float], mode: str) -> float:
    if not a_tags or not b_tags:
        return 0.0
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for key, value in a_tags.items():
        weight = tag_weight(key, mode)
        norm_a += (value**2) * weight
        if key in b_tags:
            dot += value * b_tags[key] * weight
    for key, value in b_tags.items():
        norm_b += (value**2) * tag_weight(key, mode)
    return dot / math.sqrt(norm_a * norm_b) if dot and norm_a and norm_b else 0.0


def build_reasons(
    shared: list[dict[str, Any]],
    source_tags: dict[str, float],
    candidate_tags: dict[str, float],
    tag_definitions: dict[str, dict[str, str]],
    mode: str,
) -> list[str]:
    items = []
    for item in shared:
        key = item["key"]
        prefix = tag_prefix(key)
        label = tag_definitions.get(key, {}).get("label", key)
        display_score = item["contribution"] * REASON_PRIORITY.get(prefix, 0.7)
        min_strength = min(source_tags.get(key, 0.0), candidate_tags.get(key, 0.0))
        if prefix != "status" and display_score > 0:
            items.append(
                {
                    "prefix": prefix,
                    "label": label,
                    "displayScore": display_score,
                    "minStrength": min_strength,
                }
            )
    items.sort(key=lambda x: x["displayScore"], reverse=True)
    primary = [
        item
        for item in items
        if item["prefix"] in PRIMARY_REASON_PREFIXES
        and item["minStrength"] >= (0.22 if mode == "expand" else 0.28)
    ][:3]
    fallback = [] if primary else [
        item for item in items if item["prefix"] == "selection" and item["minStrength"] >= 0.45
    ][: 3 - len(primary)]
    return [item["label"] for item in (primary + fallback)[:3]]


def reason_sentence(reasons: list[str]) -> str:
    if not reasons:
        return "嗜好タグの近さから選んだ候補です。"
    labels = reasons[:3]
    joined = "、".join(labels)
    has_texture = any(any(token in label for token in ("コシ", "香り", "喉越し", "麺")) for label in labels)
    has_style = any(
        any(token in label for token in ("讃岐", "関西", "江戸前", "信州", "越前", "出雲", "田舎", "石臼", "手打", "地域色", "セルフ"))
        for label in labels
    )
    has_dish = any(
        any(token in label for token in ("カレー", "釜", "ぶっかけ", "肉", "味噌", "きしめん", "稲庭", "鴨", "天ぷら", "十割"))
        for label in labels
    )
    has_scene = any(any(token in label for token in ("昼食", "短時間", "目的地", "酒", "蕎麦前", "落ち着いた")) for label in labels)
    has_mood = any(any(token in label for token in ("伝統", "老舗", "現代的", "個性派", "翁", "藪", "更科", "砂場")) for label in labels)
    if has_texture and (has_style or has_dish):
        return f"麺や味の方向性が近い候補です（{joined}）。"
    if has_scene and (has_style or has_texture or has_dish):
        return f"使い方や店の方向性が近い候補です（{joined}）。"
    if has_mood or has_scene:
        return f"店の雰囲気や訪れ方が近い候補です（{joined}）。"
    if has_style or has_dish:
        return f"料理の系統が近い候補です（{joined}）。"
    return f"近い特徴を持つ候補です（{joined}）。"


def display_scores(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not items:
        return items
    max_score = max(item["score"] for item in items)
    min_score = min(item["score"] for item in items)
    spread = max_score - min_score
    output = []
    for index, item in enumerate(items):
        rank_score = max(72, 96 - (index * 4))
        value_score = 72 + (((item["score"] - min_score) / spread) * 24) if spread > 0.03 else rank_score
        output.append({**item, "displayScore": round(max(72, min(96, (value_score * 0.62) + (rank_score * 0.38))))})
    return output


def affinity_index(groups: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for group in groups:
        urls = group.get("urls")
        if not isinstance(urls, list) or len(urls) < 2:
            continue
        for url in urls:
            result.setdefault(url, []).append(group)
    return result


def affinity_boost(source_url: str, candidate_url: str, mode: str, index: dict[str, list[dict[str, Any]]]) -> float:
    boost = 0.0
    for group in index.get(source_url, []):
        urls = group.get("urls") or []
        modes = group.get("modes") or []
        if candidate_url not in urls:
            continue
        if modes and mode not in modes:
            continue
        try:
            boost += float(group.get("boost", 0))
        except (TypeError, ValueError):
            continue
    return min(0.16, boost)


def recommendations(
    source: dict[str, Any],
    mode: str,
    restaurants: list[dict[str, Any]],
    tag_records: dict[str, dict[str, Any]],
    tag_definitions: dict[str, dict[str, str]],
    affinity: dict[str, list[dict[str, Any]]],
    limit: int,
) -> list[dict[str, Any]]:
    source_record = tag_records.get(source["url"])
    if not source_record:
        return []
    source_tags = tag_map(source_record)
    results = []
    for candidate in restaurants:
        if candidate["url"] == source["url"] or candidate.get("closed"):
            continue
        candidate_record = tag_records.get(candidate["url"])
        if not candidate_record:
            continue
        candidate_tags = tag_map(candidate_record)
        if not source_tags or not candidate_tags:
            continue

        dot = norm_a = norm_b = 0.0
        shared = []
        for key, a_value in source_tags.items():
            weight = tag_weight(key, mode)
            norm_a += (a_value**2) * weight
        for key, b_value in candidate_tags.items():
            norm_b += (b_value**2) * tag_weight(key, mode)
        for key, a_value in source_tags.items():
            if key not in candidate_tags:
                continue
            weight = tag_weight(key, mode)
            contribution = a_value * candidate_tags[key] * weight
            dot += contribution
            if weight > 0:
                shared.append({"key": key, "contribution": contribution})
        if not dot or not norm_a or not norm_b:
            continue
        similarity = dot / math.sqrt(norm_a * norm_b)
        if mode == "nearby" and similarity < 0.18:
            continue
        dist = distance_km(source, candidate)
        distance_score = 1 / (1 + dist / 18) if math.isfinite(dist) else 0.0
        score = similarity
        if mode == "nearby":
            score = (similarity * 0.5) + (distance_score * 0.5)
        elif mode == "expand":
            same_category = source["category"] == candidate["category"]
            same_prefecture = source["prefecture"] == candidate["prefecture"]
            novelty_factor = (0.94 if same_category else 1.08) * (0.96 if same_prefecture else 1.03)
            score = similarity * novelty_factor
        boost = affinity_boost(source["url"], candidate["url"], mode, affinity)
        if boost > 0:
            score *= 1 + boost
        if score <= 0.02:
            continue
        reasons = build_reasons(shared, source_tags, candidate_tags, tag_definitions, mode)
        results.append(
            {
                "restaurant": candidate,
                "score": score,
                "similarity": similarity,
                "affinityBoost": boost,
                "distanceKm": dist,
                "reasons": reasons,
                "reasonText": reason_sentence(reasons),
            }
        )
    results.sort(key=lambda x: x["score"], reverse=True)
    return display_scores(results[:limit])


def case_status(case: dict[str, Any], recs: list[dict[str, Any]]) -> dict[str, Any]:
    top3_urls = [item["restaurant"]["url"] for item in recs[:3]]
    topn_urls = [item["restaurant"]["url"] for item in recs]
    preferred = case.get("preferredUrls") or []
    avoid_categories = set(case.get("avoidCategories") or [])
    return {
        "preferredTop3": [url for url in preferred if url in top3_urls],
        "preferredTopN": [url for url in preferred if url in topn_urls],
        "avoidCategoryHits": [
            item["restaurant"]["name"]
            for item in recs[:3]
            if item["restaurant"].get("category") in avoid_categories
        ],
    }


def print_markdown_report(
    cases: list[dict[str, Any]],
    restaurants: list[dict[str, Any]],
    tag_records: dict[str, dict[str, Any]],
    tag_definitions: dict[str, dict[str, str]],
    affinity: dict[str, list[dict[str, Any]]],
    top: int,
) -> None:
    by_url = {r["url"]: r for r in restaurants}
    print("# Recommendation Golden Set Report")
    print()
    print("This report is informational. Review misses manually before changing scoring rules.")
    print()
    total = top3 = topn = avoid_hits = 0
    for case in cases:
        source = by_url.get(case["sourceUrl"])
        if not source:
            print(f"## {case['id']}")
            print(f"- ERROR: source not found: {case['sourceUrl']}")
            print()
            continue
        recs = recommendations(source, case.get("mode", "similar"), restaurants, tag_records, tag_definitions, affinity, top)
        status = case_status(case, recs)
        total += 1
        top3 += 1 if status["preferredTop3"] else 0
        topn += 1 if status["preferredTopN"] else 0
        avoid_hits += len(status["avoidCategoryHits"])

        print(f"## {case['id']}")
        print()
        print(f"- Source: {source['name']} ({source['prefecture']} / {source.get('area', '')})")
        print(f"- Mode: `{case.get('mode', 'similar')}`")
        print(f"- Intent: {case.get('intent', '')}")
        if top == 3:
            print(f"- Preferred hit: top3={len(status['preferredTop3'])}")
        else:
            print(f"- Preferred hit: top3={len(status['preferredTop3'])}, top{top}={len(status['preferredTopN'])}")
        if status["avoidCategoryHits"]:
            print(f"- Avoid-category hits in top3: {', '.join(status['avoidCategoryHits'])}")
        print()
        for index, item in enumerate(recs[:top], start=1):
            r = item["restaurant"]
            dist = f"{item['distanceKm']:.1f}km" if math.isfinite(item["distanceKm"]) else "-"
            print(
                f"{index}. {r['name']} ({r['prefecture']} / {r.get('area', '')}) "
                f"score={item['displayScore']} raw={item['score']:.3f} sim={item['similarity']:.3f} "
                f"affinity={item['affinityBoost']:.2f} dist={dist}"
            )
            print(f"   - {item['reasonText']}")
        print()
    print("## Summary")
    print()
    print(f"- cases: {total}")
    print(f"- preferred hit in top3: {top3}/{total}")
    print(f"- preferred hit in top{top}: {topn}/{total}")
    print(f"- avoid-category hits in top3: {avoid_hits}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate recommendation golden-set cases.")
    parser.add_argument("--case", help="Only evaluate one case id.")
    parser.add_argument("--top", type=int, default=MAX_LIMIT, help="Number of recommendations to show.")
    args = parser.parse_args()

    restaurants = load_restaurants()
    tags = load_json(RECOMMENDATION_TAGS)
    golden = load_json(GOLDEN_SET)
    tag_records = {record["url"]: record for record in tags.get("restaurants", [])}
    tag_definitions = tags.get("tagDefinitions", {})
    affinity = affinity_index(tags.get("affinityGroups") or [])
    cases = golden.get("cases", [])
    if args.case:
        cases = [case for case in cases if case.get("id") == args.case]
        if not cases:
            raise SystemExit(f"case not found: {args.case}")
    print_markdown_report(cases, restaurants, tag_records, tag_definitions, affinity, max(1, args.top))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
