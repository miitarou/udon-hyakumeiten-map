#!/usr/bin/env python3
"""Generate a small version manifest for public restaurant data."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASETS = {
    "udon": ROOT / "data" / "udon.json",
    "soba": ROOT / "data" / "soba.json",
}
OUTPUT = ROOT / "data" / "data-version.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    datasets = {}

    for key, path in DATASETS.items():
        data = json.loads(path.read_text(encoding="utf-8"))
        datasets[key] = {
            "path": f"data/{path.name}",
            "records": len(data),
            "sha256": sha256(path),
        }

    payload = {
        "version": 1,
        "generatedAt": generated_at,
        "datasets": datasets,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
