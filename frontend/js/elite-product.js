/**
 * Modern Elegance — product detail page.
 */
(function () {
  const SIZES = ["XS", "S", "M", "L", "XL", "XXL"];
  let product = null;
  let selectedSize = "M";

  function escapeHtml(str) {
    const d = document.createElement("div");
    d.textContent = String(str ?? "");
    return d.innerHTML;
  }

  function getIdFromUrl() {
    return new URLSearchParams(location.search).get("id");
  }

  function renderGallery(p) {
    const hero = document.getElementById("main-hero-image");
    const thumbs = document.getElementById("gallery-thumbs");
    if (hero) {
      hero.src = p.image;
      hero.alt = p.name;
    }
    if (thumbs) {
      thumbs.innerHTML = `
        <button type="button" class="gallery-thumb active w-full aspect-[3/4] rounded-sm overflow-hidden bg-surface-container-low">
          <img class="w-full h-full object-cover" src="${escapeHtml(p.image)}" alt="" referrerpolicy="no-referrer" />
        </button>`;
    }
  }

  function renderSizes() {
    const wrap = document.getElementById("size-grid");
    if (!wrap) return;
    wrap.innerHTML = SIZES.map(
      (s) =>
        `<button type="button" data-size="${s}" class="size-btn py-3 border rounded-sm font-label-lg text-label-lg transition-colors ${
          s === selectedSize
            ? "border-2 border-primary bg-primary-container text-white"
            : "border-outline-variant text-on-surface hover:border-primary"
        }">${s}</button>`
    ).join("");

    wrap.querySelectorAll(".size-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        selectedSize = btn.dataset.size;
        renderSizes();
      });
    });
  }

  function renderProduct(p) {
    product = p;
    document.title = `${p.name} | Modern Elegance`;
    const title = document.getElementById("product-title");
    const price = document.getElementById("product-price");
    if (title) title.textContent = p.name;
    if (price) price.textContent = formatPrice(p.price);
    const meta = document.getElementById("product-vton-meta");
    if (meta) {
      meta.textContent = `${vtonCategoryLabel(p.category)} · ${garmentTypeLabel(p.garment_type)}`;
    }

    renderGallery(p);
    renderSizes();

    document.getElementById("btn-add-bag")?.addEventListener("click", () => {
      EliteCart.add(p, { size: selectedSize });
      EliteCart.openDrawer();
    });

    document.getElementById("btn-try-on")?.addEventListener("click", () => {
      EliteVTON.open(p);
    });

    document.getElementById("btn-vto-float")?.addEventListener("click", () => {
      EliteVTON.open(p);
    });

    const related = document.getElementById("related-grid");
    if (related) {
      const others = PRODUCTS.filter((x) => x.gender === p.gender && x.id !== p.id).slice(0, 4);
      related.innerHTML = "";
      others.forEach((item) => {
        const card = document.createElement("a");
        card.href = `product.html?id=${encodeURIComponent(item.id)}`;
        card.className = "group cursor-pointer block";
        card.innerHTML = `
          <div class="relative aspect-[3/4] mb-4 bg-surface-container-low rounded-lg overflow-hidden shadow-sm">
            <img alt="" class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105" src="${escapeHtml(item.image)}" referrerpolicy="no-referrer" />
          </div>
          <h3 class="font-headline-md text-primary text-sm mb-1 truncate">${escapeHtml(item.name)}</h3>
          <p class="font-body-md text-on-surface-variant">${formatPrice(item.price)}</p>`;
        related.appendChild(card);
      });
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    const id = getIdFromUrl();
    const p = id ? getProduct(id) : null;
    if (!p) {
      window.location.replace("index.html");
      return;
    }
    renderProduct(p);
  });
})();
