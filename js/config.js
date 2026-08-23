/**
 * API URL for the try-on widget.
 *
 * Local dev  → http://127.0.0.1:8081
 * Production → your AWS Lightsail HTTPS URL (set PRODUCTION_API below)
 */
const PRODUCTION_API = ""; // e.g. "https://vton-api.xxxxx.us-east-1.cs.amazonlightsail.com"

const isLocal =
  location.hostname === "localhost" || location.hostname === "127.0.0.1";

const VTON_CONFIG = {
  API_BASE: isLocal ? "http://127.0.0.1:8081" : PRODUCTION_API,
  API_ENABLED: true,
};

if (!isLocal && !VTON_CONFIG.API_BASE) {
  console.warn(
    "[VTON] Set PRODUCTION_API in js/config.js to your Lightsail URL, then redeploy Vercel."
  );
}
