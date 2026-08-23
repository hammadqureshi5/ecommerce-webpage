/**
 * API URL for the try-on widget.
 *
 * - Local shop (localhost:8080) → local backend (127.0.0.1:8081)
 * - Vercel / any live site → your deployed backend (HTTPS), NOT localhost
 *
 * After you deploy the backend to Cloud Run, set PRODUCTION_API below
 * and redeploy the frontend to Vercel.
 */
const PRODUCTION_API = "https://thursday-investing-suits-injection.trycloudflare.com";

const isLocal =
  location.hostname === "localhost" || location.hostname === "127.0.0.1";

const VTON_CONFIG = {
  API_BASE: isLocal ? "http://127.0.0.1:8081" : PRODUCTION_API,
  API_ENABLED: true,
};

if (!isLocal && !VTON_CONFIG.API_BASE) {
  console.warn(
    "[VTON] Set PRODUCTION_API in js/config.js to your deployed backend URL, then redeploy to Vercel."
  );
}
