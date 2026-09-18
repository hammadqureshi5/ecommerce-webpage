# VTON Demo — Phase 2 Backend

Simple HTTP API for virtual try-on. Any website can call it with a person photo
and a garment photo. The server classifies clothing, picks a prompt, builds a
mask, calls Flux, and returns the result image(s).

```text
Website  →  POST /api/generate
         →  garment face-crop → classify → CSV → prompt → mask → Flux
```

The browser never talks to Flux. Set `FLUX_BASE_URL` in `.env` only.

Routing uses the **tested** files in this folder:

- `vton_supported_combinations.csv`
- `prompts/` (active `.txt` files only; `DISCARD/` is ignored)

## Module tests (no Flux GPU call)

Test each stage independently. Artifacts land in `test_output/`.

```bash
cd vton-demo/backend
python test_modules.py                 # all modules
python test_modules.py combinations    # CSV lookup
python test_modules.py prompts         # prompt resolution for every CSV row
python test_modules.py preprocess      # garment face detect + crop
python test_modules.py classify        # SigLIP person + garment labels
python test_modules.py mask            # person clothing-agnostic mask
python test_modules.py dry             # crop → classify → CSV → prompt (stops before Flux)
```

Optional image paths:

```bash
python test_modules.py preprocess ..\images\f-dress-red.jpg
python test_modules.py classify ..\images\m-suit-navy.jpg ..\images\m-shirt-blue.jpg
python test_modules.py dry ..\images\m-suit-navy.jpg ..\images\f-dress-red.jpg
```

| Module | What it checks | Output |
|--------|----------------|--------|
| `preprocess` | Face found → crop below chin; else leave image | `04_garment_preprocess.json`, `04_crop_*.png` |
| `classify` | Person → `person_outfit`, garment → `garment_type` | `05_classify.json` |
| `prompts` | Right `.txt` for each CSV combo | `02_prompts.json` |
| `dry` | Full path except Flux | `06_pipeline_dry.json`, `06_prompt.txt` |

## Setup

```bash
cd vton-demo/backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env
# Edit .env and set FLUX_BASE_URL to your Flux GPU server
```

## Run

```bash
python app.py
```

API listens on **http://127.0.0.1:8081** (override with `PORT` in `.env`).

Check health:

```bash
curl http://127.0.0.1:8081/health
```

## Smoke test (curl)

Replace the person path with your photo; garment can come from the demo shop:

```bash
curl -X POST http://127.0.0.1:8081/api/generate ^
  -F "image_a=@C:\path\to\person.jpg" ^
  -F "image_b=@C:\Users\DELL\Desktop\vton-demo\images\m-shirt-blue.jpg" ^
  -F "garment_type=shirt"
```

On macOS / Linux:

```bash
curl -X POST http://127.0.0.1:8081/api/generate \
  -F "image_a=@/path/to/person.jpg" \
  -F "image_b=@../images/m-shirt-blue.jpg" \
  -F "garment_type=shirt"
```

Successful response shape:

```json
{
  "images": ["base64..."],
  "seed": 12345,
  "classification": {
    "person_outfit": "shirt_pant",
    "garment_type": "shirt",
    "vton_type": "upper_body",
    "prompt_label": "shirt_pant__to__shirt"
  }
}
```

Save the first image (PowerShell):

```powershell
$r = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8081/api/generate `
  -Form @{
    image_a = Get-Item person.jpg
    image_b = Get-Item ..\images\m-shirt-blue.jpg
    garment_type = "shirt"
  }
[IO.File]::WriteAllBytes("out.png", [Convert]::FromBase64String($r.images[0]))
```

## Integrate from any website

```javascript
const form = new FormData();
form.append("image_a", personFile);          // user photo
form.append("image_b", garmentFile);         // product image
form.append("garment_type", "shirt");        // optional but better if known

const res = await fetch("http://127.0.0.1:8081/api/generate", {
  method: "POST",
  body: form,
});
const data = await res.json();
if (!res.ok) throw new Error(data.error || "try-on failed");
// show data.images[0] as: "data:image/png;base64," + data.images[0]
```

## Request fields

| Field | Required | Meaning |
|-------|----------|---------|
| `image_a` | yes | Person photo (file) |
| `image_b` | yes | Garment photo (file) |
| `garment_type` | no | CSV type (`shirt`, `pant`, `tshirt`, …). Skips garment classification |
| `person_outfit` | no | CSV outfit (`shirt_pant`, …). Skips person classification |
| `vton_type` | no | `upper_body` / `lower_body` / `full_body` |
| `use_mask` | no | Default on; set `0` to disable |
| `seed`, `width`, `height`, … | no | Optional Flux knobs |

## Folder layout

```text
backend/
  app.py                 # Flask routes
  pipeline.py            # crop → classify → CSV → prompt → mask → Flux
  garment_preprocess.py  # face detect + crop garment below chin
  classify.py            # SigLIP → CSV labels
  clothing_taxonomy.py   # label prompts for SigLIP
  combinations.py        # CSV lookup
  prompts.py             # load prompts/*.txt
  mask.py                # YOLO clothing-agnostic person image
  flux_client.py         # Flux job submit + poll (FLUX_BASE_URL)
  test_modules.py        # per-module tests → test_output/
  vton_supported_combinations.csv
  prompts/               # full_body / upper_body / lower_body .txt files
```

## Notes

- First request may be slow: SigLIP and YOLO weights download/load once.
- Generation can take up to ~5 minutes while Flux runs.
- Phase 3 will deploy this API to Cloud Run and wire the demo shop UI.
