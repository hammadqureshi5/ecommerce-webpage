"""Client for the Flux `/generate-multi` async pipeline.

Protocol:
    POST  {FLUX_BASE_URL}/generate-multi   -> {"job_id": "...", "status": "queued"}
    GET   {FLUX_BASE_URL}/status/<job_id>  -> {"status": "...", "download_url": "..."}
    GET   <download_url>                   -> raw PNG bytes

FLUX_BASE_URL must be set in the environment (see .env.example).
Never hardcode the Flux host in this file.
"""
from __future__ import annotations

import base64
import logging
import os
import time
from typing import Any

import requests


log = logging.getLogger(__name__)

SUBMIT_TIMEOUT_S = 60
STATUS_TIMEOUT_S = 15
DOWNLOAD_TIMEOUT_S = 60
POLL_INTERVAL_S = 2.0
MAX_POLL_S = 300.0

# Must match the Flux /generate-multi form fields used by the lab app.
SCALAR_FIELDS = (
    "num_images_per_prompt",
    "num_inference_steps",
    "guidance_scale",
    "seed",
    "width",
    "height",
)


class FluxError(RuntimeError):
    """Raised when the Flux endpoint or its job pipeline returns an error."""

    def __init__(self, status: int, body: str) -> None:
        super().__init__(f"Flux returned {status}: {body[:500]}")
        self.status = status
        self.body = body


def _base_url() -> str:
    url = (os.environ.get("FLUX_BASE_URL") or "").strip().rstrip("/")
    if not url:
        raise FluxError(
            500,
            "FLUX_BASE_URL is not set. Copy .env.example to .env and set it.",
        )
    return url


def _flux_hint(status: int, base: str) -> str:
    """Short hint when Flux URL is likely misconfigured."""
    if status != 404:
        return ""
    if "127.0.0.1" in base or "localhost" in base:
        return (
            " FLUX_BASE_URL looks like a local address. Port 5000 is often your "
            "old VTON lab UI, not the Flux GPU server. Set FLUX_BASE_URL in "
            "backend/.env to your GCP Flux host (same as Desktop/VTON flux_client.py)."
        )
    return " Check that FLUX_BASE_URL points to the Flux GPU /generate-multi endpoint."


def check_reachable() -> dict:
    """Quick probe: POST /generate-multi with no body should not be 404 if URL is right."""
    base = _base_url()
    url = f"{base}/generate-multi"
    try:
        r = requests.post(url, timeout=10)
    except requests.ConnectionError as e:
        return {
            "ok": False,
            "flux_url": base,
            "error": (
                f"Cannot connect to Flux at {base}. "
                "Is the GPU VM running and FLUX_BASE_URL correct?"
            ),
            "detail": str(e)[:200],
        }
    except requests.RequestException as e:
        return {"ok": False, "flux_url": base, "error": str(e)[:200]}

    # 400/422 = endpoint exists but payload missing; 404 = wrong server/path.
    if r.status_code == 404:
        return {
            "ok": False,
            "flux_url": base,
            "error": (
                f"{base}/generate-multi returned 404."
                + _flux_hint(404, base)
            ),
        }
    return {"ok": True, "flux_url": base, "probe_status": r.status_code}


def generate(prompt: str, images_b64: list[str], **overrides: Any) -> dict:
    """Submit a job, wait for completion, return `{"images": [...], "job_id"}`.

    `images_b64` is a list of base64-encoded image strings (no data: URI prefix).
    """
    if not prompt:
        raise FluxError(400, "prompt is required")
    if not images_b64 or len(images_b64) < 1:
        raise FluxError(400, "at least one image is required")

    base = _base_url()
    generate_url = f"{base}/generate-multi"

    form_data: dict[str, Any] = {"prompt": prompt}
    extras = {
        k: overrides[k]
        for k in SCALAR_FIELDS
        if overrides.get(k) not in (None, "")
    }
    form_data.update(extras)

    files: list[tuple[str, tuple[str, bytes, str]]] = []
    for i, b64 in enumerate(images_b64):
        if not b64:
            continue
        try:
            raw = base64.b64decode(b64, validate=False)
        except Exception as e:
            raise FluxError(400, f"image {i} is not valid base64: {e}") from e
        files.append(("images", (f"input_{i}.png", raw, "image/png")))

    if not files:
        raise FluxError(400, "no decodable images provided")

    log.info("submitting Flux job to %s with %s", generate_url, extras or "upstream defaults")
    try:
        submit_resp = requests.post(
            generate_url,
            data=form_data,
            files=files,
            timeout=SUBMIT_TIMEOUT_S,
        )
    except requests.ConnectionError as e:
        raise FluxError(
            502,
            f"Cannot connect to Flux at {base}. "
            f"Check FLUX_BASE_URL in backend/.env (not the local lab UI on :5000). "
            f"Detail: {e}",
        ) from e

    if not submit_resp.ok and extras and 400 <= submit_resp.status_code < 500:
        log.warning(
            "upstream rejected scalar fields (%s); retrying without them",
            submit_resp.status_code,
        )
        try:
            submit_resp = requests.post(
                generate_url,
                data={"prompt": prompt},
                files=files,
                timeout=SUBMIT_TIMEOUT_S,
            )
        except requests.ConnectionError as e:
            raise FluxError(502, f"Cannot connect to Flux at {base}: {e}") from e

    if not submit_resp.ok:
        hint = _flux_hint(submit_resp.status_code, base)
        raise FluxError(submit_resp.status_code, submit_resp.text + hint)

    try:
        submit_body = submit_resp.json()
    except ValueError as e:
        raise FluxError(502, f"submit returned non-JSON: {submit_resp.text[:300]}") from e

    job_id = submit_body.get("job_id")
    if not job_id:
        raise FluxError(502, f"submit returned no job_id: {submit_body}")

    download_urls = _poll_for_completion(base, job_id)

    images_out: list[str] = []
    for url in download_urls:
        try:
            images_out.append(download_url_as_b64(url))
        except Exception as e:
            raise FluxError(502, f"failed to download {url}: {e}") from e

    return {"images": images_out, "job_id": job_id}


def _poll_for_completion(base: str, job_id: str) -> list[str]:
    """Poll `/status/<job_id>` until completed. Return download URL list."""
    status_url = f"{base}/status/{job_id}"
    deadline = time.monotonic() + MAX_POLL_S

    while True:
        if time.monotonic() > deadline:
            raise FluxError(504, f"job {job_id} did not complete within {MAX_POLL_S:.0f}s")

        try:
            r = requests.get(status_url, timeout=STATUS_TIMEOUT_S)
        except requests.RequestException:
            time.sleep(POLL_INTERVAL_S)
            continue
        if not r.ok:
            raise FluxError(r.status_code, r.text)

        try:
            payload = r.json()
        except ValueError as e:
            raise FluxError(502, f"/status returned non-JSON: {r.text[:200]}") from e

        last_payload = payload if isinstance(payload, dict) else {}
        status = last_payload.get("status")

        if status == "failed" or "error" in last_payload:
            raise FluxError(502, f"upstream job failed: {last_payload}")

        if status == "completed":
            url = last_payload.get("download_url")
            if not url:
                raise FluxError(502, f"completed without download_url: {last_payload}")
            if isinstance(url, list):
                return url
            return [url]

        time.sleep(POLL_INTERVAL_S)


def download_url_as_b64(url: str) -> str:
    """Download an HTTP(S) image and return it base64-encoded (no prefix)."""
    r = requests.get(url, timeout=DOWNLOAD_TIMEOUT_S)
    r.raise_for_status()
    return base64.b64encode(r.content).decode("ascii")
