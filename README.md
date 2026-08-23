# VTON Demo — Outfit Store + Try-On Widget

A demo **online outfit store** with an optional **virtual try-on widget** on each product.

## What this does

- **Shop** (`index.html`): browse Men / Women by store categories (Tops, Pants, Outfits)
- **Try on**: click **Try on** on any product → modal widget opens (no separate VTON page)
- **Backend** (`backend/`): separate API — connect later via `js/config.js`

## How to open the shop

```bash
cd vton-demo
python -m http.server 8080
```

Open: http://127.0.0.1:8080

## Connect the widget to the API (when ready)

Edit `js/config.js`:

```javascript
API_BASE: "http://127.0.0.1:8081",
API_ENABLED: true,
```

Run the backend (`backend/README.md`), then use **Try on** in the shop.

## Folder structure

```text
vton-demo/
  index.html              # Outfit store
  try-on.html             # Redirects to index (old links)
  css/style.css
  js/
    config.js             # API_BASE, API_ENABLED
    products.js           # catalog (+ hidden vton fields)
    shop.js               # store UI
    vton-widget.js        # try-on modal
  images/
  backend/                # Phase 2 API (independent)
```

## Phases

| Phase | Status | What |
|-------|--------|------|
| 1 | **Done** | Store UI + VTON widget (modal) |
| 2 | **Done** | Backend API (local) |
| 3 | Waiting | Deploy + set `API_ENABLED: true` on production URL |

## Future API call

```text
POST {API_BASE}/api/generate

Form fields:
  image_a  = person photo (file)
  image_b  = garment image (file)
  garment_type, vton_type (optional hints from product data)
```
