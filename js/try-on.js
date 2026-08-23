/**
 * Try-on page logic (Phase 1 — dummy only).
 *
 * Flow:
 *   1. Read ?product= from URL
 *   2. Show the selected garment (real photo)
 *   3. User uploads their person photo
 *   4. "Generate" shows what WOULD be sent to the API (no real call yet)
 */

(function () {
  const params = new URLSearchParams(window.location.search);
  const productId = params.get("product");
  const product = getProduct(productId);

  const selectedEl = document.getElementById("selected-product");
  const uploadZone = document.getElementById("upload-zone");
  const fileInput = document.getElementById("person-photo");
  const previewImg = document.getElementById("person-preview");
  const generateBtn = document.getElementById("generate-btn");
  const resultArea = document.getElementById("result-area");
  const apiPreview = document.getElementById("api-preview");
  const apiPreviewText = document.getElementById("api-preview-text");

  let personFile = null;

  if (!product) {
    selectedEl.innerHTML = `
      <p style="color: #c0392b">Product not found. <a href="index.html">Go back to shop</a></p>
    `;
    uploadZone.style.display = "none";
    generateBtn.style.display = "none";
    return;
  }

  const catLabel =
    CATEGORIES.find((c) => c.id === product.category)?.label || product.category;

  selectedEl.innerHTML = `
    <img class="thumb-img" src="${product.image}" alt="${product.name}" />
    <div class="details">
      <h3>${product.name}</h3>
      <p>${product.description}</p>
      <p><strong>Gender:</strong> ${product.gender} &nbsp;|&nbsp;
         <strong>Category:</strong> ${catLabel} &nbsp;|&nbsp;
         <strong>Type:</strong> ${product.garment_type}</p>
    </div>
  `;

  fileInput.addEventListener("change", () => {
    if (fileInput.files[0]) handleFile(fileInput.files[0]);
  });

  uploadZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadZone.classList.add("dragover");
  });

  uploadZone.addEventListener("dragleave", () => {
    uploadZone.classList.remove("dragover");
  });

  uploadZone.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadZone.classList.remove("dragover");
    if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
  });

  function handleFile(file) {
    if (!file.type.startsWith("image/")) {
      alert("Please upload an image file.");
      return;
    }
    personFile = file;
    previewImg.src = URL.createObjectURL(file);
    previewImg.classList.add("visible");
    generateBtn.disabled = false;
  }

  generateBtn.addEventListener("click", () => {
    if (!personFile) return;

    const apiRequest = {
      endpoint: "POST /api/generate  (Cloud Run — not connected yet)",
      fields: {
        image_a: `person photo: ${personFile.name} (${Math.round(personFile.size / 1024)} KB)`,
        image_b: `garment: ${product.name} (${product.image})`,
        vton_type: product.category,
        garment_type: product.garment_type,
        gender: product.gender,
      },
      note: "Backend will classify both images, build mask, pick prompt, call Flux.",
    };

    apiPreviewText.textContent = JSON.stringify(apiRequest, null, 2);
    apiPreview.style.display = "block";

    resultArea.innerHTML = `
      <div style="text-align: center; padding: 2rem;">
        <p style="font-size: 2rem; margin: 0 0 0.5rem">⏳</p>
        <p><strong>Phase 1 — simulated only</strong></p>
        <p style="color: #6b7280; font-size: 0.85rem">
          In Phase 3 this area will show the generated try-on image.
        </p>
      </div>
    `;
  });
})();
