#!/usr/bin/env python
"""
Master pipeline runner for the Vellore Crime News Analysis pipeline.

Stages (run in order):
  1. dataset_builder/validate_data.py   -- clean & validate   -> news_cleaned.csv
  2. scripts/enrich_locations.py        -- geocode & enrich   -> news_geocoded.csv
  3. scripts/classify_crimes.py          -- re-classify Other -> news_location_enriched.csv
  4. scripts/score_crime_risk.py         -- severity scoring   -> news_scored_final.csv

Usage:
    python scripts/run_pipeline.py            # all stages
    python scripts/run_pipeline.py --skip 1,4  # skip stages 1 and 4
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STAGES = [
    ("validate_data",  PROJECT_ROOT / "scripts" / "dataset_builder" / "validate_data.py"),
    ("enrich_locations", PROJECT_ROOT / "scripts" / "enrich_locations.py"),
    ("classify_crimes",  PROJECT_ROOT / "scripts" / "classify_crimes.py"),
    ("score_crime_risk", PROJECT_ROOT / "scripts" / "score_crime_risk.py"),
]


def main() -> int:
    skip = set()
    args = sys.argv[1:]
    if "--skip" in args:
        i = args.index("--skip")
        if i + 1 < len(args):
            skip = set(int(x.strip()) for x in args[i + 1].split(","))
    if "--help" in args:
        print(__doc__)
        return 0

    for idx, (name, script) in enumerate(STAGES, start=1):
        if idx in skip:
            print(f"[{'SKIP':>4}] Stage {idx}: {name}")
            continue
        if not script.exists():
            print(f"[{'WARN':>4}] Stage {idx}: {name} — script not found at {script}")
            continue
        print(f"[{'RUN':>4}] Stage {idx}: {name}")
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(PROJECT_ROOT),
        )
        if result.returncode != 0:
            print(f"[{'FAIL':>4}] Stage {idx}: {name} exited with code {result.returncode}")
            return result.returncode
        print()

    print("Pipeline complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
