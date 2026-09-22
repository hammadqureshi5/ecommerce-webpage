"""Build a garment-agnostic version of the person image.

The remote model tends to copy the silhouette of whatever the person is already
wearing, which is why a knee-length kurta stays knee-length even when the prompt
asks for a waist-length shirt. Standard virtual try-on pipelines avoid this by
feeding a "clothing-agnostic" person image: the garment area is painted over
with flat grey so there is no hem, no outline and no fabric left to copy.

We locate that area with two small YOLO models (pose for the body landmarks,
segmentation for the person outline), so only the person's own pixels are
touched — the background, face and hands are left exactly as they were.

Everything here degrades gracefully: if a model is unavailable or no person is
detected, the original image is returned unchanged and the caller carries on.
"""
from __future__ import annotations

import logging

import cv2
import numpy as np


log = logging.getLogger(__name__)

POSE_WEIGHTS = "yolo11n-pose.pt"
SEG_WEIGHTS = "yolo11n-seg.pt"

# COCO keypoint indices used by the YOLO pose model.
NOSE = 0
L_SHOULDER, R_SHOULDER = 5, 6
L_WRIST, R_WRIST = 9, 10
L_HIP, R_HIP = 11, 12
L_KNEE, R_KNEE = 13, 14
L_ANKLE, R_ANKLE = 15, 16

# How far the masked band reaches, as a multiple of torso height (shoulder→hip).
NECK_MARGIN = 0.18      # above the shoulders, to catch collars
SHORT_HEM_MARGIN = 0.25  # below the hips, for waist-length garments
LONG_HEM_MARGIN = 0.35   # below the knees, for tunics and long coats
WAIST_MARGIN = 0.10      # above the hips, to catch waistbands
HAND_RADIUS = 0.22       # search area for skin around each wrist
EDGE_GROW = 0.05         # dilation, so no rim of the old garment survives
# Lab distance that still counts as skin. Kept tight because earth-toned fabric
# sits close to skin tone, and leaking the old garment's colour is worse than
# repainting a hand the model will redraw anyway.
SKIN_TOLERANCE = 15.0

VALID_REGIONS = ("upper", "upper_long", "lower", "full")
VALID_FILLS = ("gray", "inpaint", "blur")

_models: dict[str, object] = {}


class MaskError(RuntimeError):
    """Raised when the garment region could not be located."""


def _load(weights: str):
    """Lazily load and cache a YOLO model. Weights download on first use."""
    if weights not in _models:
        from ultralytics import YOLO  # imported late: torch is slow to load

        log.info("loading %s", weights)
        _models[weights] = YOLO(weights)
    return _models[weights]


def _largest_person(result) -> int | None:
    """Index of the biggest detected box, or None when nothing was found."""
    boxes = getattr(result, "boxes", None)
    if boxes is None or len(boxes) == 0:
        return None
    xyxy = boxes.xyxy.cpu().numpy()
    areas = (xyxy[:, 2] - xyxy[:, 0]) * (xyxy[:, 3] - xyxy[:, 1])
    return int(np.argmax(areas))


def _keypoints(image: np.ndarray) -> np.ndarray:
    """Return the (17, 3) keypoint array (x, y, confidence) for the main person."""
    result = _load(POSE_WEIGHTS)(image, verbose=False)[0]
    idx = _largest_person(result)
    if idx is None or result.keypoints is None:
        raise MaskError("no person detected in the image")

    xy = result.keypoints.xy.cpu().numpy()[idx]
    conf = result.keypoints.conf
    conf = (
        conf.cpu().numpy()[idx]
        if conf is not None
        else np.ones(len(xy), dtype=np.float32)
    )
    return np.concatenate([xy, conf[:, None]], axis=1)


def _person_mask(image: np.ndarray, kps: np.ndarray) -> np.ndarray:
    """Binary mask of the main person's silhouette."""
    h, w = image.shape[:2]
    try:
        result = _load(SEG_WEIGHTS)(image, classes=[0], verbose=False)[0]
        idx = _largest_person(result)
        if idx is None or result.masks is None:
            raise MaskError("segmentation found no person")
        mask = result.masks.data.cpu().numpy()[idx]
        mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)
        return (mask > 0.5).astype(np.uint8)
    except Exception as exc:
        # Without a silhouette we would repaint the background too, so fall back
        # to the span of the visible landmarks rather than the whole frame.
        log.warning("person segmentation unavailable (%s); using body box", exc)
        visible = kps[kps[:, 2] >= 0.3]
        mask = np.zeros((h, w), dtype=np.uint8)
        if len(visible) == 0:
            return mask
        pad = 0.15 * (visible[:, 0].max() - visible[:, 0].min())
        x0 = int(np.clip(visible[:, 0].min() - pad, 0, w))
        x1 = int(np.clip(visible[:, 0].max() + pad, 0, w))
        mask[:, x0:x1] = 1
        return mask


def _point(kps: np.ndarray, *idx: int, min_conf: float = 0.3) -> float | None:
    """Mean y of the given keypoints, ignoring low-confidence ones."""
    ys = [kps[i][1] for i in idx if kps[i][2] >= min_conf]
    return float(np.mean(ys)) if ys else None


def _band(kps: np.ndarray, region: str, height: int) -> tuple[int, int]:
    """Vertical span of the garment area for this region, in pixels."""
    shoulder_y = _point(kps, L_SHOULDER, R_SHOULDER)
    hip_y = _point(kps, L_HIP, R_HIP)
    if shoulder_y is None or hip_y is None:
        raise MaskError("shoulders or hips not visible; cannot place the mask")

    torso = max(hip_y - shoulder_y, 1.0)
    knee_y = _point(kps, L_KNEE, R_KNEE)
    nose_y = _point(kps, NOSE)

    # Stop at the ankles so shoes and feet survive: every prompt promises the
    # footwear is untouched.
    ankle_y = _point(kps, L_ANKLE, R_ANKLE)
    legs_bottom = ankle_y if ankle_y is not None else float(height)

    if region == "lower":
        top = hip_y - WAIST_MARGIN * torso
        bottom = legs_bottom
    elif region == "full":
        top = shoulder_y - NECK_MARGIN * torso
        bottom = legs_bottom
    elif region == "upper_long":
        top = shoulder_y - NECK_MARGIN * torso
        bottom = (knee_y + LONG_HEM_MARGIN * torso) if knee_y else hip_y + 2.0 * torso
    else:  # "upper"
        top = shoulder_y - NECK_MARGIN * torso
        bottom = hip_y + SHORT_HEM_MARGIN * torso

    # Never paint over the face: stay below the midpoint of nose and shoulders.
    if nose_y is not None and region != "lower":
        top = max(top, nose_y + 0.5 * (shoulder_y - nose_y))

    return int(np.clip(top, 0, height)), int(np.clip(bottom, 0, height))


def _lower_garment_colour(
    image: np.ndarray, person: np.ndarray, below: int, torso: float
) -> tuple[int, int, int] | None:
    """Median colour of the lower garment, sampled just below the masked band.

    Used to repaint the area under the hips. Flat grey there costs the model all
    knowledge of the leg colour, and it fills the gap by matching the new top —
    which is how a brown shalwar comes back black.
    """
    h = image.shape[0]
    start = min(below + int(0.05 * torso), h)
    end = min(below + int(0.45 * torso), h)
    if end <= start:
        return None

    strip = image[start:end]
    inside = person[start:end].astype(bool)
    if inside.sum() < 50:
        return None

    median = np.median(strip[inside].reshape(-1, 3), axis=0)
    return tuple(int(v) for v in median)


def _protect_hands(
    mask: np.ndarray, image: np.ndarray, kps: np.ndarray, torso: float
) -> None:
    """Take the hands back out of the mask, without sparing the sleeve.

    A plain disc around the wrist would also preserve whatever the wrist rests
    against — with arms at the sides that is a patch of the very garment we are
    erasing. So inside the disc we keep only pixels that match the skin tone
    sampled from the face.
    """
    if kps[NOSE][2] < 0.3:
        return

    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB).astype(np.float32)
    h, w = mask.shape
    patch = max(int(0.08 * torso), 3)
    nx, ny = int(kps[NOSE][0]), int(kps[NOSE][1])
    face = lab[
        max(ny - patch, 0):min(ny + patch, h),
        max(nx - patch, 0):min(nx + patch, w),
    ]
    if face.size == 0:
        return
    skin = np.median(face.reshape(-1, 3), axis=0)

    radius = max(int(HAND_RADIUS * torso), 8)
    for i in (L_WRIST, R_WRIST):
        if kps[i][2] < 0.3:
            continue
        disc = np.zeros_like(mask)
        cv2.circle(disc, (int(kps[i][0]), int(kps[i][1])), radius, 1, -1)
        distance = np.linalg.norm(lab - skin, axis=2)
        mask[(disc == 1) & (distance < SKIN_TOLERANCE)] = 0


def build_agnostic(image_bytes: bytes, region: str, fill: str = "gray") -> bytes:
    """Return *image_bytes* with the garment area for *region* neutralised.

    *region* is one of ``upper``, ``upper_long``, ``lower`` or ``full``.
    *fill* is ``gray`` (flat neutral, the try-on standard), ``inpaint`` (blend
    from the surrounding pixels) or ``blur`` (destroy detail, keep colour).

    Raises MaskError when no person or no usable landmarks are found.
    """
    if region not in VALID_REGIONS:
        raise MaskError(f"unknown region: {region}")
    if fill not in VALID_FILLS:
        raise MaskError(f"unknown fill: {fill}")

    image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise MaskError("could not decode the person image")

    h = image.shape[0]
    kps = _keypoints(image)
    top, bottom = _band(kps, region, h)
    if bottom <= top:
        raise MaskError("computed an empty garment band")

    shoulder_y = _point(kps, L_SHOULDER, R_SHOULDER)
    hip_y = _point(kps, L_HIP, R_HIP)
    torso = max(hip_y - shoulder_y, 1.0)

    # Grow the silhouette slightly, otherwise a thin outline of the old garment
    # survives along the edges and the model reads it as the hem.
    grow = max(int(EDGE_GROW * torso), 3)
    person = _person_mask(image, kps)
    mask = cv2.dilate(person, np.ones((grow, grow), np.uint8))
    mask[:top, :] = 0
    mask[bottom:, :] = 0

    _protect_hands(mask, image, kps, torso)

    if not mask.any():
        raise MaskError("garment band did not overlap the person")

    if fill == "gray":
        out = image.copy()
        out[mask.astype(bool)] = (128, 128, 128)
        # Below the hips the person keeps wearing their own lower garment, so
        # repaint that part in its real colour rather than leaving it neutral.
        if region == "upper_long":
            colour = _lower_garment_colour(image, person, bottom, torso)
            if colour is not None:
                below_hip = mask.astype(bool).copy()
                below_hip[: int(hip_y), :] = False
                out[below_hip] = colour
                log.info("repainted below the hips in the lower garment's colour")
    elif fill == "inpaint":
        out = cv2.inpaint(image, mask * 255, 7, cv2.INPAINT_TELEA)
    else:  # blur
        blurred = cv2.GaussianBlur(image, (0, 0), sigmaX=max(h / 40.0, 5.0))
        out = np.where(mask[:, :, None].astype(bool), blurred, image)

    ok, encoded = cv2.imencode(".png", out)
    if not ok:
        raise MaskError("failed to encode the masked image")

    log.info("masked region=%s fill=%s band=%d-%d px", region, fill, top, bottom)
    return encoded.tobytes()


def region_for_vton_type(
    vton_type: str,
    person_outfit: str,
    garment_type: str,
) -> str | None:
    """Map CSV ``vton_type`` + labels to a mask region for ``build_agnostic``.

    Returns None when masking should be skipped (jacket/coat layering).
    """
    if garment_type in ("jacket", "coat"):
        return None

    # Accept both CSV underscores and prompt-folder hyphens.
    key = (vton_type or "").strip().replace("_", "-")

    if key == "lower-body":
        return "lower"
    if key == "full-body":
        return "full"
    if key == "upper-body":
        # Kurta hems sit below the hip; erase past the knee so Flux does not
        # copy the old length onto a shorter shirt.
        return "upper_long" if person_outfit == "kurta_shalwar" else "upper"
    return None


def region_for(
    category: str, prompt_label: str, depth: str = "auto"
) -> str | None:
    """Lab-style helper: category folder + ``person__to__garment`` label.

    Prefer ``region_for_vton_type`` in the auto API pipeline.
    """
    person_outfit, _, target = prompt_label.partition("__to__")
    if depth == "torso" and target not in ("jacket", "coat"):
        key = (category or "").strip().replace("_", "-")
        if key == "lower-body":
            return "lower"
        if key == "full-body":
            return "full"
        if key == "upper-body":
            return "upper"
        return None
    return region_for_vton_type(category, person_outfit, target)
