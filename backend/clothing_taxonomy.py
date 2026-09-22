"""Clothing labels aligned with ``vton_supported_combinations.csv``.

Person (Image 1) uses outfit classes from the CSV ``person_outfit`` column.
Garment (Image 2) uses product classes from the CSV ``garment_type`` column.

``csv_person_outfits`` / ``csv_garment_types`` expose only labels that appear
in the CSV, so SigLIP never scores a class that is not a supported category.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import combinations


@dataclass(frozen=True)
class LabelSpec:
    """One classification class and the text prompts SigLIP scores against."""

    key: str
    prompts: tuple[str, ...]


# What the person in Image 1 is wearing (CSV person_outfit).
PERSON_OUTFITS: dict[str, LabelSpec] = {
    "shirt_pant": LabelSpec(
        key="shirt_pant",
        prompts=(
            "a person wearing a shirt and pants",
            "a person in a t-shirt and trousers",
            "a person wearing a blouse and jeans",
        ),
    ),
    "kurta_shalwar": LabelSpec(
        key="kurta_shalwar",
        prompts=(
            "a person wearing a Pakistani shalwar kameez",
            "a person in a long kurta tunic and loose shalwar",
            "a person wearing a long South Asian tunic with baggy trousers",
        ),
    ),
    "suit": LabelSpec(
        key="suit",
        prompts=(
            "a person wearing a formal suit",
            "a person in a blazer and matching trousers",
        ),
    ),
}


# What Image 2 shows (CSV garment_type).
GARMENT_TYPES: dict[str, LabelSpec] = {
    "shirt": LabelSpec(
        key="shirt",
        prompts=(
            "a button-up shirt or blouse product photo",
            "a waist-length collared shirt as the main garment",
            "a person modelling a button-up shirt",
            "a t-shirt or tee product photo",
            "a casual crew-neck short-sleeve tee as the main garment",
            "a person modelling a short-sleeve striped t-shirt",
        ),
    ),
    "jacket": LabelSpec(
        key="jacket",
        prompts=(
            "a jacket or blazer product photo",
            "an outerwear jacket flat lay",
        ),
    ),
    "coat": LabelSpec(
        key="coat",
        prompts=(
            "a long coat product photo",
            "an overcoat flat lay",
        ),
    ),
    "pant": LabelSpec(
        key="pant",
        prompts=(
            "a pair of pants alone with no shirt visible",
            "casual pants or denim product flat lay showing only the bottoms",
            "a pair of jeans or casual pants alone",
        ),
    ),
    "trouser": LabelSpec(
        key="trouser",
        prompts=(
            "a pair of formal trousers alone with no shirt visible",
            "dress trousers flat lay showing only the pants",
        ),
    ),
    "shorts": LabelSpec(
        key="shorts",
        prompts=(
            "a pair of shorts alone with no shirt visible",
            "shorts product flat lay showing only the bottoms",
        ),
    ),
    "suit": LabelSpec(
        key="suit",
        prompts=(
            "a complete formal suit product photo",
            "a matching blazer and trousers outfit",
        ),
    ),
    "shirt_pant": LabelSpec(
        key="shirt_pant",
        prompts=(
            "a complete shirt and pants outfit product photo",
            "a coordinated two-piece shirt and bottom set on a model",
            "a matching t-shirt and pants outfit as one product",
        ),
    ),
    "kurta_shalwar": LabelSpec(
        key="kurta_shalwar",
        prompts=(
            "a complete kurta shalwar outfit product photo",
            "a matching shalwar kameez set",
        ),
    ),
}


@lru_cache(maxsize=1)
def csv_person_outfits() -> dict[str, LabelSpec]:
    """Person labels that appear in the CSV (taxonomy ∩ CSV)."""
    allowed = {row[1] for row in combinations.all_combos()}
    return {k: v for k, v in PERSON_OUTFITS.items() if k in allowed}


@lru_cache(maxsize=1)
def csv_garment_types() -> dict[str, LabelSpec]:
    """Garment labels that appear in the CSV (taxonomy ∩ CSV)."""
    allowed = {row[2] for row in combinations.all_combos()}
    return {k: v for k, v in GARMENT_TYPES.items() if k in allowed}


VALID_PERSON_OUTFITS = frozenset(PERSON_OUTFITS)
VALID_GARMENT_TYPES = frozenset(GARMENT_TYPES)
VALID_VTON_TYPES = frozenset({"full_body", "upper_body", "lower_body"})
