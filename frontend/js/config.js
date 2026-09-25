/**
 * API URL for the try-on widget.
 *
 * Local dev  → http://127.0.0.1:8081
 * Production → AWS Lightsail (Vercel shop calls this)
 */
const PRODUCTION_API =
  "https://container-service-1.p12vr5zrn1t66.ap-southeast-1.cs.amazonlightsail.com";

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
