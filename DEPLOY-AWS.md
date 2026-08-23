# Deploy VTON API on AWS Lightsail + billing alerts

**Architecture**

```text
Vercel (shop)  →  Lightsail HTTPS API  →  Flux GPU (GCP)
```

Frontend stays on Vercel. Only `backend/` goes to AWS.

---

## Part 1 — Billing alert (do this first, ~5 min)

Uses your **$100 credit** — get emailed before surprise charges.

### Option A: AWS Budgets (recommended)

1. Open [AWS Billing → Budgets](https://console.aws.amazon.com/billing/home#/budgets)
2. **Create budget** → **Cost budget** → **Next**
3. Budget name: `vton-monthly-alert`
4. Period: **Monthly**
5. Budget amount: **$10** (or $25)
6. **Next** → Alert threshold: **80%** and **100%** → email: your address
7. Create a second budget at **$50** if you want an extra warning
8. **Create budget**

### Option B: CloudWatch billing alarm

1. Region must be **US East (N. Virginia)** `us-east-1` for billing metrics
2. [CloudWatch → Alarms → Create alarm](https://console.aws.amazon.com/cloudwatch/)
3. Metric → **Billing** → **Total Estimated Charge**
4. Threshold: **Greater than $10**
5. Create SNS topic → subscribe your email → Create alarm

Also enable: **Billing preferences** → **Receive Free Tier Usage Alerts** and **Receive Billing Alerts**.

---

## Part 2 — Lightsail deploy (recommended: Container + HTTPS)

Lightsail **Container Service** gives a free **HTTPS** URL (required for Vercel).

### Requirements on your PC

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [AWS CLI](https://aws.amazon.com/cli/) installed
- Lightsail plugin:

```powershell
winget install Amazon.AWSCLI
winget install Docker.DockerDesktop
aws configure
```

**Lightsail plugin (Windows)** — there is no `install-plugin` command. Download `lightsailctl.exe` manually:

```powershell
$dir = "$env:USERPROFILE\bin\lightsailctl"
New-Item -ItemType Directory -Force -Path $dir
Invoke-WebRequest -Uri "https://s3.us-west-2.amazonaws.com/lightsailctl/latest/windows-amd64/lightsailctl.exe" -OutFile "$dir\lightsailctl.exe"
# Add to PATH (User) — restart terminal after this
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
[Environment]::SetEnvironmentVariable("Path", "$userPath;$dir", "User")
lightsailctl.exe --version
```

Close and reopen PowerShell, then `aws lightsail push-container-image` will work.

Enter AWS Access Key + Secret from **IAM** → your user → Security credentials → Create access key.

### Step 1 — Create container service (AWS console)

1. [Lightsail → Containers](https://lightsail.aws.amazon.com/ls/webapp/create/container)
2. **Power**: **Small** (2 GB RAM) minimum — **Medium** (4 GB) safer for PyTorch + YOLO
3. **Scale**: 1 node
4. Name: `vton-api`
5. Create container service (wait until ready)

### Step 2 — Build and push image (PowerShell on your PC)

```powershell
cd C:\Users\DELL\Desktop\vton-demo\backend

docker build -t vton-backend .

aws lightsail push-container-image `
  --service-name vton-api `
  --label vton-backend `
  --image vton-backend:latest `
  --region us-east-1
```

Copy the image name from output (looks like `:vton-backend.vton-api.1`).

### Step 3 — Deploy container

1. Edit `backend/deploy/lightsail-deployment.json`:
   - Set `"image"` to the name from step 2
   - Set `FLUX_BASE_URL` to your Flux GPU URL (no trailing slash)
   - Set `CORS_ORIGINS` to your Vercel URL

2. Deploy:

```powershell
aws lightsail create-container-service-deployment `
  --service-name vton-api `
  --cli-input-json file://deploy/lightsail-deployment.json `
  --region us-east-1
```

3. Lightsail → **vton-api** → **Deployments** — wait until **Active**
4. Copy **Public URL** (HTTPS), e.g. `https://vton-api.xxxxx.us-east-1.cs.amazonlightsail.com`

### Step 4 — Test

```powershell
curl https://YOUR-LIGHTSAIL-URL/health
```

Should return `"ok": true`.

### Step 5 — Connect Vercel

Edit `js/config.js`:

```javascript
const PRODUCTION_API = "https://YOUR-LIGHTSAIL-URL";
const isLocal = location.hostname === "localhost" || location.hostname === "127.0.0.1";
const VTON_CONFIG = {
  API_BASE: isLocal ? "http://127.0.0.1:8081" : PRODUCTION_API,
  API_ENABLED: true,
};
```

```powershell
git add js/config.js
git commit -m "Point API to AWS Lightsail"
git push
```

Vercel redeploys → test **Try on** on your live shop.

---

## Part 3 — Alternative: Lightsail Linux instance (SSH)

Cheaper to understand, but **no automatic HTTPS** (harder with Vercel).

1. Lightsail → **Create instance** → Ubuntu 22.04 → **$12/mo (2 GB)**
2. Attach **static IP**
3. Networking → firewall: open **8080**
4. Browser SSH → run:

```bash
export REPO_URL=https://github.com/hammadqureshi5/ecommerce-webpage.git
bash -c "$(curl -fsSL https://raw.githubusercontent.com/hammadqureshi5/ecommerce-webpage/main/backend/deploy/lightsail-instance-setup.sh)"
```

Or clone repo manually and run `backend/deploy/lightsail-instance-setup.sh`.

5. Edit `~/vton-api/backend/.env` → set `FLUX_BASE_URL`
6. `sudo systemctl restart vton-api`

For HTTPS on instance you need a **domain** + Caddy/nginx, or use Container Service instead.

---

## Cost estimate (from $100 credit)

| Lightsail Container Small (2 GB) | ~$10–15/mo |
| Lightsail Container Medium (4 GB) | ~$20–40/mo |
| Flux GPU (GCP) | Separate — not from AWS credit |

Stop or delete the service when not testing to save credit.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Build fails / OOM | Use Medium (4 GB) plan |
| `/health` fails | Check deployment logs in Lightsail |
| Vercel failed to fetch | API must be **HTTPS**; check `CORS_ORIGINS` |
| Flux error | Set `FLUX_BASE_URL` in deployment env (not localhost) |
| First try-on slow | SigLIP + YOLO download on first request — normal |

---

## Update API after code changes

```powershell
cd backend
docker build -t vton-backend .
aws lightsail push-container-image --service-name vton-api --label vton-backend --image vton-backend:latest --region us-east-1
# Update image tag in lightsail-deployment.json if version changed
aws lightsail create-container-service-deployment --service-name vton-api --cli-input-json file://deploy/lightsail-deployment.json --region us-east-1
```
