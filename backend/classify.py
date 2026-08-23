"""SigLIP zero-shot classification → CSV labels (person_outfit / garment_type)."""
from __future__ import annotations

import logging
import time
from io import BytesIO
from typing import Any

import numpy as np
from PIL import Image, ImageOps

from clothing_taxonomy import GARMENT_TYPES, PERSON_OUTFITS, LabelSpec

log = logging.getLogger(__name__)

MODEL_ID = "google/siglip2-base-patch16-224"
FALLBACK_MODEL_ID = "google/siglip-base-patch16-224"
HYPOTHESIS_TEMPLATE = "This is a photo of {}."

_classifier = None


class ClassificationError(RuntimeError):
    """Raised when SigLIP cannot load or complete inference."""


def get_classifier():
    """Lazy-load the SigLIP pipeline once and cache it globally."""
    global _classifier
    if _classifier is not None:
        return _classifier

    import torch
    from transformers import pipeline

    use_cuda = torch.cuda.is_available()
    device = 0 if use_cuda else -1
    dtype = torch.float16 if use_cuda else torch.float32

    log.info("Loading SigLIP (device=%s) …", device)
    t0 = time.perf_counter()
    try:
        _classifier = pipeline(
            "zero-shot-image-classification",
            model=MODEL_ID,
            device=device,
            torch_dtype=dtype,
        )
    except Exception:
        log.warning("Primary SigLIP failed; falling back to %s", FALLBACK_MODEL_ID)
        _classifier = pipeline(
            "zero-shot-image-classification",
            model=FALLBACK_MODEL_ID,
            device=device,
        )
    log.info("SigLIP loaded in %.2f s", time.perf_counter() - t0)
    return _classifier


def _open_rgb(image_bytes: bytes) -> Image.Image | None:
    try:
        with Image.open(BytesIO(image_bytes)) as opened:
            image = ImageOps.exif_transpose(opened).convert("RGB")
            image.load()
            return image
    except Exception as exc:
        log.warning("Could not decode image: %s", exc)
        return None


def _score_classes(
    image: Image.Image,
    classes: dict[str, LabelSpec],
) -> list[dict[str, Any]]:
    flat_prompts = [p for spec in classes.values() for p in spec.prompts]
    clf = get_classifier()
    try:
        raw = clf(
            image,
            candidate_labels=flat_prompts,
            hypothesis_template=HYPOTHESIS_TEMPLATE,
        )
    except Exception as exc:
        raise ClassificationError(
            "clothing analysis is temporarily unavailable"
        ) from exc

    by_prompt = {r["label"]: float(r["score"]) for r in raw}
    results: list[dict[str, Any]] = []
    for key, spec in classes.items():
        scores = [by_prompt.get(p, 0.0) for p in spec.prompts]
        results.append({
            "label": key,
            "score": round(float(np.mean(scores)), 4),
            "peak": round(float(np.max(scores)), 4),
            "best_prompt": spec.prompts[int(np.argmax(scores))],
        })
    results.sort(key=lambda d: d["score"], reverse=True)

    if len(results) > 1:
        gap = results[0]["score"] - results[1]["score"]
        results[0]["margin"] = round(gap, 4)
        results[0]["runner_up"] = results[1]["label"]
        results[0]["confident"] = bool(
            results[0]["score"] >= 0.15 and gap >= 0.03
        )
    elif results:
        results[0]["margin"] = results[0]["score"]
        results[0]["runner_up"] = None
        results[0]["confident"] = True

    return results


def classify_person(image_bytes: bytes) -> list[dict[str, Any]]:
    """Classify Image 1 → CSV ``person_outfit`` labels, best first."""
    image = _open_rgb(image_bytes)
    if image is None:
        return []
    t0 = time.perf_counter()
    results = _score_classes(image, PERSON_OUTFITS)
    log.info(
        "person classify: top=%s (%.1f%%) in %.2fs",
        results[0]["label"] if results else "?",
        (results[0]["score"] * 100) if results else 0,
        time.perf_counter() - t0,
    )
    return results


def classify_garment(image_bytes: bytes) -> list[dict[str, Any]]:
    """Classify Image 2 → CSV ``garment_type`` labels, best first."""
    image = _open_rgb(image_bytes)
    if image is None:
        return []
    t0 = time.perf_counter()
    results = _score_classes(image, GARMENT_TYPES)
    log.info(
        "garment classify: top=%s (%.1f%%) in %.2fs",
        results[0]["label"] if results else "?",
        (results[0]["score"] * 100) if results else 0,
        time.perf_counter() - t0,
    )
    return results
