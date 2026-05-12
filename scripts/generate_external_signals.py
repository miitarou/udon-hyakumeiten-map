#!/usr/bin/env python3
"""Generate deterministic external recommendation signals.

This script intentionally does not crawl pages.  The input registry stores only
short, manually reviewed evidence terms from allowed public sources.  The
script maps those terms to the existing recommendation tag dictionary so the
runtime can use external hints without fetching third-party pages or calling an
LLM/API.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "external_source_registry.json"
RECOMMENDATION_TAGS = ROOT / "data" / "recommendation_tags.json"
OUTPUT = ROOT / "data" / "external_signals.json"

SOURCE_CONFIDENCE = {
    "official_site": 0.88,
    "official_tourism": 0.84,
    "public_directory": 0.72,
    "manual_editorial_seed": 0.62,
}

# Evidence terms are intentionally short labels, not copied page text.
TERM_RULES: dict[str, tuple[tuple[str, float, float], ...]] = {
    "石臼": (("style.stone_milled", 0.84, 0.88), ("texture.aroma_focused", 0.76, 0.84)),
    "自家製粉": (("style.stone_milled", 0.86, 0.9), ("texture.aroma_focused", 0.78, 0.86)),
    "玄蕎麦": (("style.stone_milled", 0.84, 0.86), ("texture.aroma_focused", 0.76, 0.82)),
    "粗挽き": (("style.stone_milled", 0.76, 0.76), ("texture.aroma_focused", 0.7, 0.74)),
    "香り": (("texture.aroma_focused", 0.72, 0.74),),
    "手打ち": (("style.handmade", 0.84, 0.88),),
    "手打": (("style.handmade", 0.84, 0.88),),
    "純手打": (("style.handmade", 0.9, 0.9),),
    "製麺所": (("style.self_service", 0.76, 0.82), ("scene.quick_lunch", 0.68, 0.76), ("style.regional_specialty", 0.66, 0.72)),
    "食料品店": (("style.self_service", 0.72, 0.78), ("scene.quick_lunch", 0.68, 0.74), ("style.regional_specialty", 0.66, 0.72)),
    "セルフ": (("style.self_service", 0.84, 0.88), ("scene.quick_lunch", 0.72, 0.82)),
    "短時間利用": (("scene.quick_lunch", 0.72, 0.8), ("scene.solo_lunch", 0.58, 0.68)),
    "讃岐": (("style.sanuki_influenced", 0.9, 0.9), ("texture.koshi_strong", 0.78, 0.82), ("style.regional_specialty", 0.68, 0.72)),
    "コシ": (("texture.koshi_strong", 0.76, 0.78),),
    "釜玉": (("dish.kamatama", 0.86, 0.9),),
    "釜たま": (("dish.kamatama", 0.86, 0.9),),
    "釜バター": (("dish.kamatama", 0.74, 0.76), ("mood.modern", 0.58, 0.62)),
    "ぶっかけ": (("dish.bukkake", 0.84, 0.88),),
    "天ぷら": (("dish.tempura", 0.74, 0.82),),
    "半熟卵天": (("dish.tempura", 0.8, 0.84),),
    "関西だし": (("style.kansai_dashi", 0.78, 0.82),),
    "日本酒": (("scene.drink_pairing", 0.72, 0.78), ("scene.calm_meal", 0.56, 0.62)),
    "蕎麦前": (("scene.drink_pairing", 0.86, 0.9), ("scene.calm_meal", 0.66, 0.72)),
    "蕎麦会席": (("scene.drink_pairing", 0.82, 0.84), ("scene.calm_meal", 0.78, 0.82)),
    "蕎麦懐石": (("scene.drink_pairing", 0.82, 0.84), ("scene.calm_meal", 0.8, 0.84)),
    "蕎麦料理": (("scene.drink_pairing", 0.72, 0.76), ("scene.calm_meal", 0.7, 0.76)),
    "そばがき": (("scene.drink_pairing", 0.66, 0.7),),
    "落ち着いた食事": (("scene.calm_meal", 0.72, 0.78),),
    "目的地": (("scene.destination", 0.78, 0.82),),
    "地域色": (("style.regional_specialty", 0.74, 0.78),),
    "田舎そば": (("style.country_soba", 0.82, 0.84), ("style.regional_specialty", 0.68, 0.72)),
    "常陸秋そば": (("style.country_soba", 0.72, 0.76), ("style.regional_specialty", 0.78, 0.8), ("texture.aroma_focused", 0.68, 0.72)),
    "古民家": (("mood.traditional", 0.7, 0.76), ("scene.destination", 0.58, 0.64)),
    "伝統": (("mood.traditional", 0.72, 0.78),),
    "藪": (("lineage.yabu", 0.8, 0.84), ("style.edomae_soba", 0.72, 0.78)),
    "江戸前": (("style.edomae_soba", 0.78, 0.82),),
    "信州": (("style.shinshu_soba", 0.84, 0.86), ("style.regional_specialty", 0.72, 0.76)),
    "戸隠": (("style.shinshu_soba", 0.86, 0.88), ("style.regional_specialty", 0.76, 0.8), ("scene.destination", 0.7, 0.74)),
    "朝うどん": (("scene.quick_lunch", 0.72, 0.78), ("scene.solo_lunch", 0.62, 0.68)),
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def merge_signal(
    signals: dict[str, dict[str, Any]],
    key: str,
    weight: float,
    confidence: float,
    source_type: str,
    term: str,
) -> None:
    current = signals.get(key)
    evidence = f"term:{term}"
    if current is None:
        signals[key] = {
            "key": key,
            "weight": round(weight, 2),
            "confidence": round(confidence, 2),
            "source": "external_signal",
            "sourceTypes": [source_type],
            "evidence": [evidence],
        }
        return

    current_strength = float(current["weight"]) * float(current["confidence"])
    new_strength = weight * confidence
    if new_strength > current_strength:
        current["weight"] = round(weight, 2)
        current["confidence"] = round(confidence, 2)
    if source_type not in current["sourceTypes"]:
        current["sourceTypes"].append(source_type)
        current["sourceTypes"].sort()
    if evidence not in current["evidence"]:
        current["evidence"].append(evidence)
        current["evidence"].sort()


def generate_payload() -> dict[str, Any]:
    registry = load_json(REGISTRY)
    recommendation_tags = load_json(RECOMMENDATION_TAGS)
    tag_definitions = recommendation_tags.get("tagDefinitions", {})
    known_tags = set(tag_definitions)
    source_rows = registry.get("sources", [])

    grouped: dict[str, dict[str, Any]] = {}
    signal_maps: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    unmapped_terms: dict[str, list[str]] = defaultdict(list)

    for source in source_rows:
        url = source["restaurantUrl"]
        grouped.setdefault(
            url,
            {
                "url": url,
                "name": source["name"],
                "category": source["category"],
                "sourceRefs": [],
            },
        )
        grouped[url]["sourceRefs"].append(
            {
                "sourceType": source["sourceType"],
                "sourceUrl": source["sourceUrl"],
                "sourceTitle": source["sourceTitle"],
                "reviewStatus": source["reviewStatus"],
                "lastCheckedAt": source["lastCheckedAt"],
            }
        )

        source_confidence = SOURCE_CONFIDENCE.get(source["sourceType"], 0.6)
        for term in source.get("evidenceTerms", []):
            rules = TERM_RULES.get(term)
            if not rules:
                unmapped_terms[url].append(term)
                continue
            for key, weight, confidence in rules:
                if key not in known_tags:
                    unmapped_terms[url].append(term)
                    continue
                merge_signal(
                    signal_maps[url],
                    key,
                    weight,
                    min(confidence, source_confidence),
                    source["sourceType"],
                    term,
                )

    restaurants: list[dict[str, Any]] = []
    for url, item in grouped.items():
        signals = sorted(signal_maps[url].values(), key=lambda row: row["key"])
        restaurants.append(
            {
                **item,
                "signals": signals,
                "unmappedTerms": sorted(set(unmapped_terms.get(url, []))),
            }
        )

    restaurants.sort(key=lambda row: (row["category"], row["name"]))
    return {
        "version": 1,
        "generatedAt": registry.get("selection", {}).get("sampledAt"),
        "method": {
            "summary": "Deterministic external signal PoC generated from manually reviewed short evidence terms. No external fetch, raw text storage, or runtime LLM/API call.",
            "sourceConfidence": SOURCE_CONFIDENCE,
            "sample": registry.get("selection", {}),
        },
        "restaurants": restaurants,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic external recommendation signals.")
    parser.add_argument("--check", action="store_true", help="Exit non-zero if data/external_signals.json is stale.")
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
            print(f"{OUTPUT.relative_to(ROOT)} is stale. Run scripts/generate_external_signals.py", file=sys.stderr)
            return 1
        print(f"{OUTPUT.relative_to(ROOT)} is up to date.")
        return 0

    OUTPUT.write_text(text, encoding="utf-8")
    signal_count = sum(len(row["signals"]) for row in payload["restaurants"])
    unmapped_count = sum(len(row.get("unmappedTerms") or []) for row in payload["restaurants"])
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    print(f"restaurants={len(payload['restaurants'])} signals={signal_count} unmapped_terms={unmapped_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
