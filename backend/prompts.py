"""Load try-on prompts from the local ``prompts/`` tree.

Layout:
    prompts/
      upper-body/
        shirt_pant__to__shirt.txt
        _generic.txt
      lower-body/
      full-body/
"""
from __future__ import annotations

from pathlib import Path


PROMPTS_ROOT = Path(__file__).parent / "prompts"

# CSV uses underscores; folders use hyphens.
_VTON_TO_FOLDER = {
    "upper_body": "upper-body",
    "lower_body": "lower-body",
    "full_body": "full-body",
}


def folder_for(vton_type: str) -> str:
    key = (vton_type or "").strip()
    if key in _VTON_TO_FOLDER:
        return _VTON_TO_FOLDER[key]
    # Already hyphenated from older callers.
    return key.replace("_", "-")


def prompt_label(person_outfit: str, garment_type: str) -> str:
    return f"{person_outfit}__to__{garment_type}"


def get_prompt(vton_type: str, person_outfit: str, garment_type: str) -> tuple[str, str]:
    """Return ``(prompt_text, label_used)``.

    Tries the exact combo file first, then category fallbacks.
    Raises FileNotFoundError if nothing usable exists.
    """
    folder = folder_for(vton_type)
    cat_dir = PROMPTS_ROOT / folder
    label = prompt_label(person_outfit, garment_type)
    exact = cat_dir / f"{label}.txt"
    if exact.is_file():
        return exact.read_text(encoding="utf-8"), label

    # Prefer exact combo, then well-known fallbacks from the tested prompt tree.
    # Do not read DISCARD/ — only files directly in the category folder.
    for fallback in (
        "_generic.txt",
        "GENERAL.txt",
        "generic_for_shirt.txt",
        "_generic_FOR_shirt_pant kurta_shalwar.txt",
        "prompt_01.txt",
    ):
        path = cat_dir / fallback
        if path.is_file():
            return path.read_text(encoding="utf-8"), path.stem

    # Last resort: any .txt whose name looks like a generic (still skip DISCARD).
    for txt in sorted(cat_dir.glob("*.txt")):
        stem_l = txt.stem.lower()
        if "generic" in stem_l or stem_l == "general" or stem_l.startswith("prompt_"):
            return txt.read_text(encoding="utf-8"), txt.stem

    raise FileNotFoundError(
        f"no prompt found for {folder}/{label}.txt (and no fallback)"
    )
