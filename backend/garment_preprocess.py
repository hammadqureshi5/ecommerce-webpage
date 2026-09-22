"""Pre-process garment (reference) images before classification.

When a product photo shows a model face, crop away everything from the chin
upward so SigLIP (and Flux) see the garment, not the model's face. Flat-lay
or no-face images are returned unchanged.
"""
from __future__ import annotations

import logging
from io import BytesIO
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageOps

log = logging.getLogger(__name__)

POSE_WEIGHTS = "yolo11n-pose.pt"
NOSE = 0
L_SHOULDER, R_SHOULDER = 5, 6
MIN_NOSE_CONF = 0.35
MIN_SHOULDER_CONF = 0.3
# Crop starts between nose and shoulders (approx. chin line).
CHIN_FACTOR = 0.55
# Reject crops that leave almost nothing of the garment.
MIN_CROP_HEIGHT_RATIO = 0.35

_models: dict[str, object] = {}


def _load_pose():
    if POSE_WEIGHTS not in _models:
        from ultralytics import YOLO

        log.info("loading %s for garment face crop", POSE_WEIGHTS)
        _models[POSE_WEIGHTS] = YOLO(POSE_WEIGHTS)
    return _models[POSE_WEIGHTS]


def _decode_rgb(image_bytes: bytes) -> Image.Image | None:
    try:
        with Image.open(BytesIO(image_bytes)) as opened:
            image = ImageOps.exif_transpose(opened).convert("RGB")
            image.load()
            return image
    except Exception as exc:
        log.warning("garment decode failed: %s", exc)
        return None


def _largest_person_idx(result) -> int | None:
    boxes = getattr(result, "boxes", None)
    if boxes is None or len(boxes) == 0:
        return None
    xyxy = boxes.xyxy.cpu().numpy()
    areas = (xyxy[:, 2] - xyxy[:, 0]) * (xyxy[:, 3] - xyxy[:, 1])
    return int(np.argmax(areas))


def _chin_y(kps: np.ndarray, height: int) -> int | None:
    """Vertical crop line just below the chin, or None if no usable face."""
    if kps[NOSE][2] < MIN_NOSE_CONF:
        return None

    nose_y = float(kps[NOSE][1])
    shoulders = [
        kps[i][1]
        for i in (L_SHOULDER, R_SHOULDER)
        if kps[i][2] >= MIN_SHOULDER_CONF
    ]
    if not shoulders:
        # Nose alone: crop a bit below it.
        chin = int(nose_y + 0.12 * height)
    else:
        shoulder_y = float(np.mean(shoulders))
        if shoulder_y <= nose_y:
            chin = int(nose_y + 0.08 * height)
        else:
            chin = int(nose_y + CHIN_FACTOR * (shoulder_y - nose_y))

    chin = int(np.clip(chin, 0, height - 1))
    remaining = height - chin
    if remaining < int(MIN_CROP_HEIGHT_RATIO * height):
        return None
    return chin


def preprocess_garment(image_bytes: bytes) -> tuple[bytes, dict[str, Any]]:
    """Crop face region out of a garment photo when a face is present.

    Returns ``(bytes_for_downstream, meta)`` where *meta* always includes
    ``cropped`` (bool) and either crop geometry or a ``reason`` string.
    """
    image = _decode_rgb(image_bytes)
    if image is None:
        return image_bytes, {"cropped": False, "reason": "decode_failed"}

    w, h = image.size
    bgr = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    try:
        result = _load_pose()(bgr, verbose=False)[0]
    except Exception as exc:
        log.warning("pose failed on garment image: %s", exc)
        return image_bytes, {"cropped": False, "reason": "pose_failed"}

    idx = _largest_person_idx(result)
    if idx is None or result.keypoints is None:
        return image_bytes, {"cropped": False, "reason": "no_person"}

    xy = result.keypoints.xy.cpu().numpy()[idx]
    conf = result.keypoints.conf
    conf = (
        conf.cpu().numpy()[idx]
        if conf is not None
        else np.ones(len(xy), dtype=np.float32)
    )
    kps = np.concatenate([xy, conf[:, None]], axis=1)

    crop_y = _chin_y(kps, h)
    if crop_y is None:
        return image_bytes, {"cropped": False, "reason": "no_face"}

    cropped = image.crop((0, crop_y, w, h))
    buf = BytesIO()
    cropped.save(buf, format="PNG")
    out = buf.getvalue()

    meta = {
        "cropped": True,
        "crop_y": crop_y,
        "original_size": [w, h],
        "cropped_size": [cropped.size[0], cropped.size[1]],
    }
    log.info(
        "garment face crop: y=%d  %dx%d -> %dx%d",
        crop_y, w, h, cropped.size[0], cropped.size[1],
    )
    return out, meta
