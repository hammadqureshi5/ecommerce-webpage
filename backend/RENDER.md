# Render deployment (VTON API)

Deploy the **backend folder only** — not the whole shop (shop stays on Vercel).

## Render form (match these exactly)

| Field | Value |
|-------|--------|
| **Name** | `vton-api` (or any name) |
| **Language** | Python 3 |
| **Branch** | `main` |
| **Root Directory** | `backend` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn --bind 0.0.0.0:$PORT --timeout 300 --workers 1 app:app` |

Do **not** use `src` as root directory.  
Do **not** use `gunicorn your_application.wsgi` (that is for Django).

## Environment variables (Render → Environment)

| Key | Value |
|-----|--------|
| `FLUX_BASE_URL` | Your Flux GPU URL, e.g. `http://YOUR_GPU_IP:5000` |
| `CORS_ORIGINS` | `https://ecommerce-webpage-seven.vercel.app,http://localhost:8080` |

## Instance size (important)

| Plan | Will it work? |
|------|----------------|
| **Free (512 MB)** | Usually **no** — PyTorch + SigLIP + YOLO need more RAM |
| **Starter (512 MB–2 GB)** | Try **2 GB RAM** minimum recommended |
| **Standard** | Safer for ML models |

Free tier also **spins down** after idle (slow first request) and may **timeout** on long Flux jobs.

## After deploy

1. Copy your Render URL, e.g. `https://vton-api-xxxx.onrender.com`
2. In the **frontend** repo, set `PRODUCTION_API` in `js/config.js`:
   ```javascript
   const PRODUCTION_API = "https://vton-api-xxxx.onrender.com";
   ```
3. Redeploy to Vercel
4. Test: `https://vton-api-xxxx.onrender.com/health`

## Common errors

| Error | Fix |
|-------|-----|
| Start command red / Required | Use the gunicorn command above, not `.wsgi` |
| Build fails / out of memory | Use Starter 2GB+ plan |
| 502 / worker timeout | `--timeout 300` on gunicorn; upgrade plan if needed |
| CORS / failed to fetch | Set `CORS_ORIGINS` with your exact Vercel URL |
| Flux connection error | Set `FLUX_BASE_URL` in Render env (not localhost) |

## Local test with gunicorn (same as Render)

```bash
cd backend
pip install gunicorn
set FLUX_BASE_URL=http://YOUR_GPU:5000
gunicorn --bind 0.0.0.0:8081 --timeout 300 --workers 1 app:app
```
