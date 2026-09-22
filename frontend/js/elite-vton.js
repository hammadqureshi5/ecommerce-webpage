/**
 * Stitch-styled Virtual Try-On modal — calls POST /api/generate on VTON backend.
 */
const EliteVTON = (function () {
  let root = null;
  let product = null;
  let personFile = null;
  let els = {};

  function ensureDom() {
    if (root) return;

    root = document.createElement("div");
    root.id = "elite-vton";
    root.className = "fixed inset-0 z-[100] hidden items-center justify-center p-container-padding bg-scrim/40 backdrop-blur-md";
    root.setAttribute("aria-hidden", "true");
    root.innerHTML = `
      <div class="bg-surface-container-lowest w-full max-w-5xl rounded-xl shadow-[0_20px_40px_rgba(26,43,60,0.15)] overflow-hidden flex flex-col max-h-[90vh] border border-surface-variant">
        <div class="flex justify-between items-center px-stack-md py-stack-sm border-b border-surface-variant">
          <h2 class="font-headline-md text-headline-md text-primary-container">Virtual Fitting Room</h2>
          <button type="button" data-close class="p-2 text-on-surface-variant hover:text-primary-container transition-colors" aria-label="Close">
            <span class="material-symbols-outlined text-headline-md">close</span>
          </button>
        </div>
        <div class="flex-1 flex flex-col md:flex-row overflow-hidden min-h-0">
          <div class="w-full md:w-3/5 bg-surface-container-low relative flex items-center justify-center border-r border-surface-variant min-h-[280px] md:min-h-[400px]">
            <div id="vton-preview-wrap" class="absolute inset-0 flex items-center justify-center p-stack-md">
              <img id="vton-garment-preview" class="object-contain w-full h-full max-w-md mx-auto rounded-lg" alt="" />
            </div>
            <img id="vton-result-img" class="hidden absolute inset-4 object-contain w-[calc(100%-2rem)] h-[calc(100%-2rem)] mx-auto rounded-lg" alt="Try-on result" />
            <div id="vton-loading" class="hidden absolute inset-0 bg-surface-container-low/80 flex items-center justify-center">
              <p class="font-label-lg text-primary-container">Generating try-on…</p>
            </div>
          </div>
          <div class="w-full md:w-2/5 p-stack-md flex flex-col overflow-y-auto bg-surface-container-lowest">
            <div id="vton-product-info" class="mb-stack-md pb-stack-sm border-b border-surface-variant"></div>
            <div class="mb-stack-md">
              <h3 class="font-label-lg text-label-lg text-primary-container uppercase mb-stack-sm">Input Method</h3>
              <input type="file" id="vton-file-input" accept="image/*" class="hidden" />
              <div class="flex flex-col gap-unit">
                <button type="button" id="vton-upload-btn" class="w-full bg-primary-container text-on-primary-container hover:opacity-90 font-label-lg py-3 rounded flex items-center justify-center gap-2">
                  <span class="material-symbols-outlined">upload_file</span> Upload Your Photo
                </button>
              </div>
              <img id="vton-person-thumb" class="hidden mt-3 w-20 h-20 object-cover rounded-lg border border-outline-variant" alt="Your photo" />
            </div>
            <div id="vton-status" class="hidden font-body-sm mb-stack-sm rounded p-3"></div>
          </div>
        </div>
        <div class="p-stack-md border-t border-surface-variant bg-surface-container-lowest flex gap-gutter">
          <button type="button" id="vton-generate-btn" disabled class="flex-1 flex items-center justify-center gap-2 px-stack-md py-3 bg-primary-container text-on-primary-container hover:opacity-90 rounded font-label-lg disabled:opacity-40 disabled:cursor-not-allowed">
            <span class="material-symbols-outlined">view_in_ar</span> Generate Try-On
          </button>
          <button type="button" id="vton-add-bag-btn" class="flex items-center justify-center gap-2 px-stack-md py-3 border border-outline text-on-surface hover:bg-surface-container rounded font-label-lg">
            <span class="material-symbols-outlined">shopping_bag</span> Add to Bag
          </button>
        </div>
      </div>`;
    document.body.appendChild(root);

    els = {
      garmentPreview: root.querySelector("#vton-garment-preview"),
      resultImg: root.querySelector("#vton-result-img"),
      loading: root.querySelector("#vton-loading"),
      productInfo: root.querySelector("#vton-product-info"),
      fileInput: root.querySelector("#vton-file-input"),
      uploadBtn: root.querySelector("#vton-upload-btn"),
      personThumb: root.querySelector("#vton-person-thumb"),
      generateBtn: root.querySelector("#vton-generate-btn"),
      addBagBtn: root.querySelector("#vton-add-bag-btn"),
      status: root.querySelector("#vton-status"),
    };

    root.querySelectorAll("[data-close]").forEach((el) => el.addEventListener("click", close));
    root.addEventListener("click", (e) => {
      if (e.target === root) close();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !root.classList.contains("hidden")) close();
    });

    els.uploadBtn.addEventListener("click", () => els.fileInput.click());
    els.fileInput.addEventListener("change", () => {
      if (els.fileInput.files[0]) setPersonFile(els.fileInput.files[0]);
    });
    els.generateBtn.addEventListener("click", generate);
    els.addBagBtn.addEventListener("click", () => {
      if (product) {
        EliteCart.add(product, { size: "M" });
        close();
        EliteCart.openDrawer();
      }
    });
  }

  function setPersonFile(file) {
    if (!file.type.startsWith("image/")) {
      showStatus("Please upload an image file.", "error");
      return;
    }
    personFile = file;
    els.personThumb.src = URL.createObjectURL(file);
    els.personThumb.classList.remove("hidden");
    els.generateBtn.disabled = false;
    hideStatus();
  }

  function showStatus(msg, type) {
    els.status.textContent = msg;
    els.status.classList.remove("hidden", "bg-error-container", "text-on-error-container", "bg-surface-container", "text-on-surface");
    if (type === "error") els.status.classList.add("bg-error-container", "text-on-error-container");
    else els.status.classList.add("bg-surface-container", "text-on-surface");
  }

  function hideStatus() {
    els.status.classList.add("hidden");
  }

  function resetState() {
    personFile = null;
    els.fileInput.value = "";
    els.personThumb.classList.add("hidden");
    els.personThumb.src = "";
    els.resultImg.classList.add("hidden");
    els.garmentPreview.classList.remove("hidden");
    els.loading.classList.add("hidden");
    els.generateBtn.disabled = true;
    hideStatus();
  }

  function renderProduct(p) {
    els.garmentPreview.src = p.image;
    els.garmentPreview.alt = p.name;
    els.productInfo.innerHTML = `
      <h3 class="font-headline-md text-headline-md text-primary">${p.name}</h3>
      <p class="font-body-lg text-on-surface-variant mt-1">${formatPrice(p.price)}</p>`;
    els.addBagBtn.innerHTML = `<span class="material-symbols-outlined">shopping_bag</span> Add to Bag — ${formatPrice(p.price)}`;
  }

  function open(p) {
    if (!p) return;
    ensureDom();
    product = p;
    resetState();
    renderProduct(p);
    root.classList.remove("hidden");
    root.classList.add("flex");
    root.setAttribute("aria-hidden", "false");
    document.body.classList.add("overflow-hidden");
  }

  function close() {
    if (!root) return;
    root.classList.add("hidden");
    root.classList.remove("flex");
    root.setAttribute("aria-hidden", "true");
    document.body.classList.remove("overflow-hidden");
    product = null;
  }

  async function generate() {
    if (!personFile || !product) return;

    const cfg = typeof VTON_CONFIG !== "undefined" ? VTON_CONFIG : { API_ENABLED: false, API_BASE: "" };

    if (!cfg.API_ENABLED || !cfg.API_BASE) {
      showStatus("Set API_ENABLED and API_BASE in js/config.js to connect the backend.", "error");
      return;
    }

    els.generateBtn.disabled = true;
    els.loading.classList.remove("hidden");
    hideStatus();

    try {
      const health = await fetch(`${cfg.API_BASE}/health`);
      if (!health.ok) throw new Error(`Backend not reachable at ${cfg.API_BASE}`);

      const form = new FormData();
      form.append("image_a", personFile);
      form.append("garment_url", product.image);
      form.append("garment_type", product.garment_type || "shirt_pant");
      form.append("vton_type", product.category || "full_body");

      const res = await fetch(`${cfg.API_BASE}/api/generate`, { method: "POST", body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Try-on failed");
      if (!data.images?.[0]) throw new Error("No image returned from backend");

      els.garmentPreview.classList.add("hidden");
      els.resultImg.src = `data:image/png;base64,${data.images[0]}`;
      els.resultImg.classList.remove("hidden");
    } catch (err) {
      showStatus(err.message || "Something went wrong.", "error");
      els.generateBtn.disabled = false;
    } finally {
      els.loading.classList.add("hidden");
    }
  }

  return { open, close };
})();
