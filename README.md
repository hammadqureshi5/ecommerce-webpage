# VTON Demo � Phase 1 (Frontend Only)

A simple clothing shop page for virtual try-on testing.

## What this does (Phase 1)

- Shows **3 categories**: Shirt, Pant, Full body
- Shows products for **Male** and **Female**
- Lets user pick a garment and upload their **person photo**
- **Does NOT call the backend yet** � Phase 3 will connect to Cloud Run

## How to open

Double-click `index.html` or run a local server:

```bash
cd vton-demo
python -m http.server 8080
```

Then open: http://127.0.0.1:8080

## Folder structure

```text
vton-demo/
??? index.html          # Shop page (pick gender + garment)
??? try-on.html         # Upload person photo for selected garment
??? css/style.css       # All styles
??? js/
?   ??? products.js     # Product list (easy to edit)
?   ??? shop.js         # Renders the shop page
?   ??? try-on.js       # Handles photo upload (dummy for now)
??? README.md
```

## Phases

| Phase | Status | What |
|-------|--------|------|
| 1 | **Done** | Dummy shop + try-on UI |
| 2 | Waiting | Backend: classify ? mask ? Flux |
| 3 | Waiting | Deploy (Vercel + Cloud Run) + connect API |

## Future API call (Phase 3)

The try-on page will send:

```text
POST https://YOUR-CLOUD-RUN-URL/api/generate

Form fields:
  image_a  = person photo (file)
  image_b  = garment image (file or product image URL)
```

Response:

```json
{
  "images": ["base64..."],
  "classification": { "person": "...", "garment": "..." }
}
```
