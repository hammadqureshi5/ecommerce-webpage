"""Lookup helpers for ``vton_supported_combinations.csv``."""
from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path


CSV_PATH = Path(__file__).parent / "vton_supported_combinations.csv"


@lru_cache(maxsize=1)
def _rows() -> tuple[tuple[str, str, str], ...]:
    with CSV_PATH.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return tuple(
            (
                (row["vton_type"] or "").strip(),
                (row["person_outfit"] or "").strip(),
                (row["garment_type"] or "").strip(),
            )
            for row in reader
            if row.get("vton_type")
        )


def lookup_vton_type(person_outfit: str, garment_type: str) -> str | None:
    """Return the CSV ``vton_type`` for this combo, or None if unsupported."""
    for vton_type, person, garment in _rows():
        if person == person_outfit and garment == garment_type:
            return vton_type
    return None


def is_supported(vton_type: str, person_outfit: str, garment_type: str) -> bool:
    """True when the exact triple exists in the CSV."""
    want = (vton_type, person_outfit, garment_type)
    return want in _rows()
