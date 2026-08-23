"""Clothing labels aligned with ``vton_supported_combinations.csv``.

Person (Image 1) uses outfit classes: shirt_pant, kurta_shalwar, dress, suit
(CSV ``person_outfit`` values).
Garment (Image 2) uses product classes from the CSV garment_type column.
"""
from __future__ import annotations

from dataclasses import dataclass


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
    "dress": LabelSpec(
        key="dress",
        prompts=(
            "a person wearing a dress or gown",
            "a person in a one-piece dress",
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


# What Image 2 shows (CSV garment_type) — flat-lay, mannequin, or on-model.
GARMENT_TYPES: dict[str, LabelSpec] = {
    "shirt": LabelSpec(
        key="shirt",
        prompts=(
            "a button-up shirt or blouse product photo",
            "a waist-length collared shirt flat lay",
        ),
    ),
    "tshirt": LabelSpec(
        key="tshirt",
        prompts=(
            "a t-shirt or tee product photo",
            "a casual crew-neck t-shirt flat lay",
        ),
    ),
    "kurta": LabelSpec(
        key="kurta",
        prompts=(
            "a long kurta or tunic product photo",
            "a South Asian long top with side slits",
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
    "jeans": LabelSpec(
        key="jeans",
        prompts=(
            "a pair of jeans product photo",
            "denim jeans flat lay",
        ),
    ),
    "pant": LabelSpec(
        key="pant",
        prompts=(
            "a pair of pants product photo",
            "casual pants flat lay",
        ),
    ),
    "trouser": LabelSpec(
        key="trouser",
        prompts=(
            "a pair of formal trousers product photo",
            "dress trousers flat lay",
        ),
    ),
    "shorts": LabelSpec(
        key="shorts",
        prompts=(
            "a pair of shorts product photo",
            "shorts flat lay",
        ),
    ),
    "shalwar": LabelSpec(
        key="shalwar",
        prompts=(
            "a pair of shalwar trousers product photo",
            "loose South Asian shalwar pants",
        ),
    ),
    "dress": LabelSpec(
        key="dress",
        prompts=(
            "a one-piece dress product photo",
            "a dress flat lay or on a mannequin",
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
            "a coordinated two-piece shirt and bottom set",
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

VALID_PERSON_OUTFITS = frozenset(PERSON_OUTFITS)
VALID_GARMENT_TYPES = frozenset(GARMENT_TYPES)
VALID_VTON_TYPES = frozenset({"full_body", "upper_body", "lower_body"})
