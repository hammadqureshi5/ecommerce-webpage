/**
 * Virtual try-on widget — modal overlay, independent of shop layout.
 *
 * Opens via VTONWidget.open(product). Calls the backend API when
 * VTON_CONFIG.API_ENABLED is true; otherwise shows a preview state.
 */
const VTONWidget = (function () {
  let root = null;
  let product = null;
  let personFile = null;

  let els = {};

  function ensureDom() {
    if (root) return;

    root = document.createElement("div");
    root.id = "vton-widget";
    root.className = "vton-widget";
    root.setAttribute("aria-hidden", "true");
    root.innerHTML = `
      <div class="vton-backdrop" data-close></div>
      <div class="vton-dialog" role="dialog" aria-modal="true" aria-labelledby="vton-title">
        <button type="button" class="vton-close" data-close aria-label="Close">&times;</button>
        <h2 id="vton-title">Virtual try-on</h2>
        <p class="vton-subtitle">Upload your photo to see how this outfit looks on you.</p>

        <div class="vton-product" id="vton-product"></div>

        <label class="upload-zone" id="vton-upload-zone">
          <input type="file" id="vton-person-photo" accept="image/*" />
          <strong>Click or drop your photo here</strong>
          <p>Full-body or upper-body photo works best</p>
        </label>
        <img id="vton-person-preview" class="preview-img" alt="Your photo preview" />

        <button type="button" id="vton-generate-btn" class="primary-btn" disabled>
          Generate try-on
        </button>

        <div id="vton-status" class="vton-status" hidden></div>

        <section class="vton-result-section">
          <h3>Result</h3>
          <div id="vton-result" class="result-placeholder">
            Your try-on result will appear here.
          </div>
        </section>
      </div>
    `;
    document.body.appendChild(root);

    els = {
      product: root.querySelector("#vton-product"),
      uploadZone: root.querySelector("#vton-upload-zone"),
      fileInput: root.querySelector("#vton-person-photo"),
      preview: root.querySelector("#vton-person-preview"),
      generateBtn: root.querySelector("#vton-generate-btn"),
      status: root.querySelector("#vton-status"),
      result: root.querySelector("#vton-result"),
    };

    root.querySelectorAll("[data-close]").forEach((el) => {
      el.addEventListener("click", close);
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && root.classList.contains("open")) close();
    });

    els.fileInput.addEventListener("change", () => {
      if (els.fileInput.files[0]) setPersonFile(els.fileInput.files[0]);
    });

    els.uploadZone.addEventListener("dragover", (e) => {
      e.preventDefault();
      els.uploadZone.classList.add("dragover");
    });
    els.uploadZone.addEventListener("dragleave", () => {
      els.uploadZone.classList.remove("dragover");
    });
    els.uploadZone.addEventListener("drop", (e) => {
      e.preventDefault();
      els.uploadZone.classList.remove("dragover");
      if (e.dataTransfer.files[0]) setPersonFile(e.dataTransfer.files[0]);
    });

    els.generateBtn.addEventListener("click", generate);
  }

  function setPersonFile(file) {
    if (!file.type.startsWith("image/")) {
      alert("Please upload an image file.");
      return;
    }
    personFile = file;
    els.preview.src = URL.createObjectURL(file);
    els.preview.classList.add("visible");
    els.generateBtn.disabled = false;
  }

  function showStatus(message, type) {
    els.status.hidden = false;
    els.status.className = "vton-status" + (type ? " " + type : "");
    els.status.textContent = message;
  }

  function hideStatus() {
    els.status.hidden = true;
    els.status.textContent = "";
  }

  function renderProduct(p) {
    els.product.innerHTML = `
      <img class="thumb-img" src="${p.image}" alt="${p.name}" />
      <div class="details">
        <h3>${p.name}</h3>
        <p class="product-price">${formatPriceHtml(p)}</p>
      </div>
    `;
  }

  function resetState() {
    personFile = null;
    els.fileInput.value = "";
    els.preview.src = "";
    els.preview.classList.remove("visible");
    els.generateBtn.disabled = true;
    hideStatus();
    els.result.innerHTML = "Your try-on result will appear here.";
    els.result.className = "result-placeholder";
  }

  function open(p) {
    ensureDom();
    product = p;
    resetState();
    renderProduct(p);
    root.classList.add("open");
    root.setAttribute("aria-hidden", "false");
    document.body.classList.add("vton-open");
    els.generateBtn.focus();
  }

  function close() {
    if (!root) return;
    root.classList.remove("open");
    root.setAttribute("aria-hidden", "true");
    document.body.classList.remove("vton-open");
    product = null;
  }

  async function fetchGarmentBlob(imageUrl) {
    const res = await fetch(imageUrl);
    if (!res.ok) throw new Error("Could not load garment image");
    return res.blob();
  }

  async function generate() {
    if (!personFile || !product) return;

    els.generateBtn.disabled = true;
    showStatus("Generating… this can take a few minutes.", "loading");

    if (!VTON_CONFIG.API_ENABLED) {
      els.result.innerHTML = `
        <div class="vton-preview-note">
          <p><strong>Widget ready — API not connected yet</strong></p>
          <p>When you enable <code>API_ENABLED</code> in <code>config.js</code>,
             this will call <code>POST ${VTON_CONFIG.API_BASE}/api/generate</code>.</p>
        </div>
      `;
      els.result.className = "";
      showStatus("Preview mode. Turn on API_ENABLED to call the backend.", "info");
      els.generateBtn.disabled = false;
      return;
    }

    try {
      const garmentBlob = await fetchGarmentBlob(product.image);
      const form = new FormData();
      form.append("image_a", personFile);
      form.append("image_b", garmentBlob, "garment.jpg");
      form.append("garment_type", product.garment_type);
      form.append("vton_type", product.category);

      const res = await fetch(`${VTON_CONFIG.API_BASE}/api/generate`, {
        method: "POST",
        body: form,
      });
      const data = await res.json();

      if (!res.ok) {
        const detail = data.body ? ` (${String(data.body).slice(0, 120)}…)` : "";
        throw new Error((data.error || "Try-on failed") + detail);
      }

      els.result.innerHTML = `<img src="data:image/png;base64,${data.images[0]}" alt="Try-on result" class="vton-result-img" />`;
      els.result.className = "";
      hideStatus();
    } catch (err) {
      showStatus(err.message || "Something went wrong.", "error");
      els.generateBtn.disabled = false;
    }
  }

  return { open, close };
})();
