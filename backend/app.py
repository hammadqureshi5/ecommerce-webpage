"""Simple VTON API — any website can call this.

Routes:
    GET  /health         — liveness
    POST /api/generate   — person + garment → try-on image(s)

Run:
    copy .env.example .env   # set FLUX_BASE_URL
    python app.py
"""
from __future__ import annotations

import logging
import os
import traceback

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import RequestEntityTooLarge

import flux_client
import pipeline
from classify import ClassificationError

load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

# Allow your Vercel shop (and localhost) to call this API.
_cors_origins = os.environ.get("CORS_ORIGINS", "*")
CORS(
    app,
    origins=[o.strip() for o in _cors_origins.split(",") if o.strip()],
    supports_credentials=False,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("vton-api")


@app.errorhandler(RequestEntityTooLarge)
def handle_too_large(_e: RequestEntityTooLarge):
    limit_mb = app.config["MAX_CONTENT_LENGTH"] / (1024 * 1024)
    return jsonify({
        "error": f"Upload too large. Both images together must stay under {limit_mb:.0f} MB.",
    }), 413


@app.get("/")
def index():
    """Simple HTML landing page for browsers."""
    flux_set = bool((os.environ.get("FLUX_BASE_URL") or "").strip())
    flux_status = "configured" if flux_set else "not set — edit backend/.env"
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>VTON Demo API</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 40rem; margin: 3rem auto; padding: 0 1rem; line-height: 1.5; color: #1a1a1a; }}
    code {{ background: #f2f2f2; padding: 0.15rem 0.4rem; border-radius: 4px; }}
    li {{ margin: 0.4rem 0; }}
  </style>
</head>
<body>
  <h1>VTON Demo API</h1>
  <p>Backend is running. This is an API, not the shop UI.</p>
  <ul>
    <li><a href="/health"><code>GET /health</code></a> — liveness check</li>
    <li><code>POST /api/generate</code> — person + garment try-on</li>
  </ul>
  <p><strong>Flux:</strong> {flux_status}</p>
  <p>Shop UI: open <code>index.html</code> with a static server (port 8080), not this API port.</p>
</body>
</html>
"""
    return html


@app.get("/health")
def health():
    flux_set = bool((os.environ.get("FLUX_BASE_URL") or "").strip())
    out = {"ok": True, "flux_configured": flux_set}
    if flux_set:
        probe = flux_client.check_reachable()
        out["flux"] = probe
        if not probe.get("ok"):
            out["ok"] = False
    return jsonify(out)


@app.post("/api/generate")
def api_generate():
    """Accept two images, run classify → mask → prompt → Flux, return JSON.

    multipart/form-data fields:
        image_a       — person photo (required file)
        image_b       — garment photo (file) OR garment_url (http URL)
        garment_url   — optional garment image URL (server-side fetch; avoids browser CORS)
        garment_type  — optional CSV garment_type (skips garment classify)
        person_outfit — optional CSV person_outfit (skips person classify)
        vton_type     — optional upper_body | lower_body | full_body
        use_mask      — optional "0"/"false" to disable masking (default on)
        seed, num_inference_steps, guidance_scale, width, height,
        num_images_per_prompt — optional Flux knobs
    """
    try:
        person = _read_file("image_a")
        garment = _read_file("image_b")
        if garment is None:
            garment = _fetch_url(request.form.get("garment_url", "").strip())
        if person is None or garment is None:
            return jsonify({
                "error": "two images are required: image_a (person) and image_b or garment_url",
            }), 400

        use_mask = request.form.get("use_mask", "1").strip().lower() not in (
            "0", "false", "off", "no",
        )

        overrides: dict = {}
        for key in (
            "num_images_per_prompt",
            "num_inference_steps",
            "width",
            "height",
            "seed",
        ):
            raw = request.form.get(key)
            if raw not in (None, ""):
                overrides[key] = int(raw)
        g = request.form.get("guidance_scale")
        if g not in (None, ""):
            overrides["guidance_scale"] = float(g)

        result = pipeline.run_try_on(
            person,
            garment,
            garment_type=(request.form.get("garment_type") or "").strip() or None,
            person_outfit=(request.form.get("person_outfit") or "").strip() or None,
            vton_type=(request.form.get("vton_type") or "").strip() or None,
            use_mask=use_mask,
            flux_overrides=overrides or None,
        )
        return jsonify(result)

    except pipeline.PipelineError as e:
        return jsonify({"error": str(e)}), 400
    except ClassificationError as e:
        return jsonify({"error": str(e)}), 503
    except flux_client.FluxError as e:
        log.warning("Flux error: %s", e)
        return jsonify({"error": str(e), "body": e.body}), 502
    except Exception as e:
        log.error("Unhandled: %s\n%s", e, traceback.format_exc())
        return jsonify({"error": f"{type(e).__name__}: {e}"}), 500


def _read_file(field: str) -> bytes | None:
    f = request.files.get(field)
    if f and f.filename:
        return f.read()
    return None


def _fetch_url(url: str) -> bytes | None:
    """Download a garment image server-side (Breakout CDN blocks browser CORS)."""
    if not url or not (url.startswith("http://") or url.startswith("https://")):
        return None
    try:
        import urllib.request

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; VTON-Demo/1.0)",
                "Referer": "https://www.breakout.com.pk/",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            if not data:
                return None
            log.info("Fetched garment_url (%s bytes) from %s", len(data), url[:80])
            return data
    except Exception as e:
        log.warning("garment_url fetch failed: %s", e)
        raise pipeline.PipelineError(f"Could not download garment image: {e}") from e


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8081"))
    # Generations can take minutes; disable the reloader so it does not
    # kill an in-flight request when a file changes.
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
