"""Load try-on prompts for CSV-supported combinations only.

Only combinations listed in ``vton_supported_combinations.csv`` are valid.
Each combo must have its own ``.txt`` under ``prompts/{upper,lower,full}_body/``.
No generic fallbacks and nothing is read from ``DISCARD/``.
"""
from __future__ import annotations

from pathlib import Path

import combinations


PROMPTS_ROOT = Path(__file__).parent / "prompts"

# Prefer underscore folders (current layout); fall back to hyphenated names.
_VTON_FOLDERS = {
    "upper_body": ("upper_body", "upper-body"),
    "lower_body": ("lower_body", "lower-body"),
    "full_body": ("full_body", "full-body"),
}


def folder_for(vton_type: str) -> str:
    """Return the first existing prompts subfolder for this vton_type."""
    key = (vton_type or "").strip()
    candidates = _VTON_FOLDERS.get(key)
    if candidates:
        for name in candidates:
            if (PROMPTS_ROOT / name).is_dir():
                return name
        return candidates[0]
    underscored = key.replace("-", "_")
    hyphenated = key.replace("_", "-")
    for name in (underscored, hyphenated, key):
        if (PROMPTS_ROOT / name).is_dir():
            return name
    return underscored

def prompt_label(person_outfit: str, garment_type: str) -> str:
    return f"{person_outfit}__to__{garment_type}"


def _title(s: str) -> str:
    return "_".join(part[:1].upper() + part[1:] for part in s.split("_"))


def candidate_filenames(person_outfit: str, garment_type: str) -> list[str]:
    """Filename stems for one CSV row (your repo uses several naming styles)."""
    p, g = person_outfit, garment_type
    names: list[str] = []
    seen: set[str] = set()

    def add(stem: str) -> None:
        if stem not in seen:
            seen.add(stem)
            names.append(stem)

    add(f"{p}__to__{g}")
    add(f"{p}_to_{g}")
    add(f"{p}-{g}")
    add(f"{_title(p)}_to_{_title(g)}")
    add(f"{_title(p)}__to__{_title(g)}")

    if p == "shirt_pant":
        add(f"pant_shirt__to__{g}")
        add(f"pant_shirt_to_{g}")
    if g == "shirt_pant":
        add(f"{p}__to__pant_shirt")
        add(f"{p}_to_pant_shirt")

    return [f"{stem}.txt" for stem in names]


def get_prompt(vton_type: str, person_outfit: str, garment_type: str) -> tuple[str, str]:
    """Return ``(prompt_text, label_used)`` for an exact CSV triple.

    Raises FileNotFoundError if the combo is unsupported or has no prompt file.
    """
    if not combinations.is_supported(vton_type, person_outfit, garment_type):
        raise FileNotFoundError(
            f"combo not in CSV: {vton_type}, {person_outfit}, {garment_type}"
        )

    folder = folder_for(vton_type)
    cat_dir = PROMPTS_ROOT / folder
    if not cat_dir.is_dir():
        raise FileNotFoundError(f"prompt folder missing: {folder}")

    for filename in candidate_filenames(person_outfit, garment_type):
        path = cat_dir / filename
        if path.is_file():
            return path.read_text(encoding="utf-8"), path.stem

    label = prompt_label(person_outfit, garment_type)
    raise FileNotFoundError(
        f"no prompt file for CSV row {vton_type}/{person_outfit}/{garment_type} "
        f"(expected one of: {', '.join(candidate_filenames(person_outfit, garment_type))})"
    )


def list_coverage() -> list[dict]:
    """Prompt file status for every CSV row (for tests)."""
    rows = []
    for vton_type, person_outfit, garment_type in combinations.all_combos():
        try:
            _, label = get_prompt(vton_type, person_outfit, garment_type)
            rows.append({
                "vton_type": vton_type,
                "person_outfit": person_outfit,
                "garment_type": garment_type,
                "prompt": label,
                "ok": True,
            })
        except FileNotFoundError as e:
            rows.append({
                "vton_type": vton_type,
                "person_outfit": person_outfit,
                "garment_type": garment_type,
                "prompt": None,
                "ok": False,
                "error": str(e),
            })
    return rows
