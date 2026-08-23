"""End-to-end try-on: classify → CSV lookup → prompt → mask → Flux.

Read ``run_try_on`` top-to-bottom — that is the whole product path.
"""
from __future__ import annotations

import base64
import logging
import random
from typing import Any

import classify
import combinations
import flux_client
import mask as mask_mod
import prompts as prompts_mod
from clothing_taxonomy import VALID_GARMENT_TYPES, VALID_PERSON_OUTFITS, VALID_VTON_TYPES

log = logging.getLogger(__name__)


class PipelineError(ValueError):
    """Bad input or unsupported clothing combo (maps to HTTP 400)."""


def run_try_on(
    person_bytes: bytes,
    garment_bytes: bytes,
    *,
    garment_type: str | None = None,
    vton_type: str | None = None,
    person_outfit: str | None = None,
    use_mask: bool = True,
    flux_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run one try-on and return a JSON-ready dict.

    Parameters
    ----------
    person_bytes, garment_bytes
        Raw image file bytes.
    garment_type
        Optional CSV garment_type from the shop. Skips garment classification.
    person_outfit
        Optional override (mainly for tests). Otherwise classified from person.
    vton_type
        Optional override. Otherwise taken from the CSV row.
    use_mask
        When True (default), paint out the old garment on the person image.
    flux_overrides
        Optional Flux knobs (seed, steps, width, …).
    """
    if not person_bytes or not garment_bytes:
        raise PipelineError("both image_a (person) and image_b (garment) are required")

    # ── 1. Classify ──────────────────────────────────────────────────────
    if person_outfit:
        person_outfit = person_outfit.strip()
        if person_outfit not in VALID_PERSON_OUTFITS:
            raise PipelineError(f"unknown person_outfit: {person_outfit}")
        person_meta = {"label": person_outfit, "score": None, "source": "client"}
    else:
        person_results = classify.classify_person(person_bytes)
        if not person_results:
            raise PipelineError("could not classify the person photo")
        person_outfit = person_results[0]["label"]
        person_meta = {**person_results[0], "source": "classifier"}

    if garment_type:
        garment_type = garment_type.strip()
        if garment_type not in VALID_GARMENT_TYPES:
            raise PipelineError(f"unknown garment_type: {garment_type}")
        garment_meta = {"label": garment_type, "score": None, "source": "client"}
    else:
        garment_results = classify.classify_garment(garment_bytes)
        if not garment_results:
            raise PipelineError("could not classify the garment photo")
        garment_type = garment_results[0]["label"]
        garment_meta = {**garment_results[0], "source": "classifier"}

    # ── 2. Validate combo via CSV ────────────────────────────────────────
    if vton_type:
        vton_type = vton_type.strip()
        if vton_type not in VALID_VTON_TYPES:
            raise PipelineError(f"unknown vton_type: {vton_type}")
        if not combinations.is_supported(vton_type, person_outfit, garment_type):
            raise PipelineError(
                f"unsupported combo: vton_type={vton_type}, "
                f"person_outfit={person_outfit}, garment_type={garment_type}"
            )
    else:
        resolved = combinations.lookup_vton_type(person_outfit, garment_type)
        if not resolved:
            raise PipelineError(
                f"unsupported combo: person_outfit={person_outfit}, "
                f"garment_type={garment_type}"
            )
        vton_type = resolved

    # ── 3. Load prompt ───────────────────────────────────────────────────
    try:
        prompt_text, prompt_label = prompts_mod.get_prompt(
            vton_type, person_outfit, garment_type
        )
    except FileNotFoundError as e:
        raise PipelineError(str(e)) from e

    # ── 4. Mask person image (optional, on by default) ───────────────────
    person_for_flux = person_bytes
    mask_region = None
    if use_mask:
        mask_region = mask_mod.region_for_vton_type(
            vton_type, person_outfit, garment_type
        )
        if mask_region:
            try:
                person_for_flux = mask_mod.build_agnostic(person_bytes, mask_region)
            except Exception as e:
                log.warning("masking failed, using original person image: %s", e)
                mask_region = None

    images_b64 = [
        base64.b64encode(person_for_flux).decode("ascii"),
        base64.b64encode(garment_bytes).decode("ascii"),
    ]

    # ── 5. Call Flux ─────────────────────────────────────────────────────
    overrides = dict(flux_overrides or {})
    seed = overrides.get("seed")
    if seed is None:
        seed = random.randrange(2**31 - 1)
        overrides["seed"] = seed

    result = flux_client.generate(prompt_text, images_b64, **overrides)

    # ── 6. Return ────────────────────────────────────────────────────────
    return {
        "images": result.get("images", []),
        "job_id": result.get("job_id"),
        "seed": seed,
        "classification": {
            "person_outfit": person_outfit,
            "garment_type": garment_type,
            "vton_type": vton_type,
            "prompt_label": prompt_label,
            "mask_region": mask_region,
            "person": person_meta,
            "garment": garment_meta,
        },
    }
