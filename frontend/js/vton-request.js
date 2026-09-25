/* Shared request handling and bounded photo uploads for virtual try-on. */
window.VtonRequest = {
  async json(url, options = {}, stage = "Generation", timeoutMs = 420000) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    const start = Date.now();
    try {
      const response = await fetch(url, { ...options, signal: controller.signal, cache: "no-store" });
      const text = await response.text();
      let data;
      try { data = JSON.parse(text); } catch {
        throw new Error(`${stage} returned HTTP ${response.status} without a valid response. The server may be restarting or the request may have timed out. Please try again shortly.`);
      }
      if (!response.ok) throw new Error(data.error || `${stage} failed (HTTP ${response.status}).`);
      return data;
    } catch (error) {
      if (error.name === "AbortError") {
        throw new Error(`${stage} timed out after ${Math.round(timeoutMs / 1000)} seconds. The server may still be processing; wait before retrying.`);
      }
      if (error instanceof TypeError) {
        const seconds = Math.round((Date.now() - start) / 1000);
        console.error("[VTON] Request failed", { url, stage, seconds, error });
        throw new Error(`${stage} connection failed after ${seconds}s. Check your internet connection. If it persists, the backend may have restarted or blocked this website. Refresh the page before retrying.`);
      }
      throw error;
    } finally { clearTimeout(timer); }
  },

  async photo(file) {
    if (file.size > 25 * 1024 * 1024) throw new Error("Please use a photo smaller than 25 MB.");
    const url = URL.createObjectURL(file);
    try {
      const image = new Image();
      await new Promise((resolve, reject) => {
        image.onload = resolve;
        image.onerror = () => reject(new Error("This photo could not be opened. Please use a JPEG, PNG or WebP image."));
        image.src = url;
      });
      const scale = Math.min(1, 1600 / Math.max(image.naturalWidth, image.naturalHeight));
      const canvas = document.createElement("canvas");
      canvas.width = Math.max(1, Math.round(image.naturalWidth * scale));
      canvas.height = Math.max(1, Math.round(image.naturalHeight * scale));
      const ctx = canvas.getContext("2d");
      if (!ctx) throw new Error("Your browser could not prepare this photo. Please try another browser.");
      ctx.fillStyle = "white";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
      const blob = await new Promise(resolve => canvas.toBlob(resolve, "image/jpeg", 0.9));
      if (!blob) throw new Error("Photo preparation failed. Please try another image.");
      return blob;
    } finally { URL.revokeObjectURL(url); }
  }
};
