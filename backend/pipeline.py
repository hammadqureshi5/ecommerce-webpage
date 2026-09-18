"""End-to-end try-on: crop → classify → CSV → prompt → mask → Flux.

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
import garment_preprocess
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

    Order of operations:
        1. Face-crop the garment image when a model face is present
        2. Classify person + garment into CSV labels
        3. Resolve vton_type from the CSV combo
        4. Load the matching prompt file
        5. Mask the person (optional)
        6. Call Flux
    """
    if not person_bytes or not garment_bytes:
        raise PipelineError("both image_a (person) and image_b (garment) are required")

    # ── 0. Garment face crop ─────────────────────────────────────────────
    garment_for_pipeline, crop_meta = garment_preprocess.preprocess_garment(
        garment_bytes
    )

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
        # Classify the (possibly cropped) garment so faces do not bias SigLIP.
        garment_results = classify.classify_garment(garment_for_pipeline)
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
        base64.b64encode(garment_for_pipeline).decode("ascii"),
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
            "garment_crop": crop_meta,
            "person": person_meta,
            "garment": garment_meta,
        },
    }


def dry_run(
    person_bytes: bytes,
    garment_bytes: bytes,
    *,
    garment_type: str | None = None,
    person_outfit: str | None = None,
    vton_type: str | None = None,
    use_mask: bool = True,
) -> dict[str, Any]:
    """Same as ``run_try_on`` but stops before Flux — for module testing."""
    if not person_bytes or not garment_bytes:
        raise PipelineError("both image_a (person) and image_b (garment) are required")

    garment_for_pipeline, crop_meta = garment_preprocess.preprocess_garment(
        garment_bytes
    )

    person_results = classify.classify_person(person_bytes) if not person_outfit else None
    if person_outfit:
        person_outfit = person_outfit.strip()
        if person_outfit not in VALID_PERSON_OUTFITS:
            raise PipelineError(f"unknown person_outfit: {person_outfit}")
        person_meta = {"label": person_outfit, "score": None, "source": "client"}
    else:
        if not person_results:
            raise PipelineError("could not classify the person photo")
        person_outfit = person_results[0]["label"]
        person_meta = {**person_results[0], "source": "classifier"}

    garment_results = (
        classify.classify_garment(garment_for_pipeline) if not garment_type else None
    )
    if garment_type:
        garment_type = garment_type.strip()
        if garment_type not in VALID_GARMENT_TYPES:
            raise PipelineError(f"unknown garment_type: {garment_type}")
        garment_meta = {"label": garment_type, "score": None, "source": "client"}
    else:
        if not garment_results:
            raise PipelineError("could not classify the garment photo")
        garment_type = garment_results[0]["label"]
        garment_meta = {**garment_results[0], "source": "classifier"}

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

    prompt_text, prompt_label = prompts_mod.get_prompt(
        vton_type, person_outfit, garment_type
    )

    mask_region = None
    if use_mask:
        mask_region = mask_mod.region_for_vton_type(
            vton_type, person_outfit, garment_type
        )

    return {
        "person_outfit": person_outfit,
        "garment_type": garment_type,
        "vton_type": vton_type,
        "prompt_label": prompt_label,
        "prompt_preview": prompt_text[:220] + ("..." if len(prompt_text) > 220 else ""),
        "prompt_full": prompt_text,
        "mask_region": mask_region,
        "garment_crop": crop_meta,
        "person": person_meta,
        "garment": garment_meta,
        "person_classify": person_results,
        "garment_classify": garment_results,
    }
