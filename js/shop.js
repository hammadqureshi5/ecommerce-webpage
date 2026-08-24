/**
 * Breakout homepage renderer.
 */
(function () {
  function escapeHtml(str) {
    if (str == null) return "";
    const d = document.createElement("div");
    d.textContent = String(str);
    return d.innerHTML;
  }

  function createProductCard(product) {
    const card = document.createElement("article");
    card.className = "bo-product";
    card.dataset.productId = product.id;

    const media = document.createElement("div");
    media.className = "bo-product__media";

    const img = document.createElement("img");
    img.alt = product.name || "";
    img.loading = "lazy";
    img.referrerPolicy = "no-referrer";
    img.src = product.image || "";
    img.onerror = function () {
      this.style.display = "none";
      media.style.background = "#e8e8e8";
    };
    media.appendChild(img);

    if (product.onSale) {
      const badge = document.createElement("span");
      badge.className = "bo-badge";
      badge.textContent = "-50%";
      media.appendChild(badge);
    }

    const quick = document.createElement("button");
    quick.type = "button";
    quick.className = "bo-quick-add";
    quick.textContent = "Choose options";
    quick.addEventListener("click", (e) => {
      e.stopPropagation();
      ProductModal.open(product);
    });
    media.appendChild(quick);
    media.addEventListener("click", () => ProductModal.open(product));

    const info = document.createElement("div");
    info.className = "bo-product__info";
    info.innerHTML = `
      <h3 class="bo-product__title">${escapeHtml(product.name)}</h3>
      <div class="bo-product__price">${formatPriceHtml(product)}</div>
    `;

    card.appendChild(media);
    card.appendChild(info);
    return card;
  }

  function renderFeaturedGrid(genderId, categories) {
    const firstCat = categories[0]?.id;
    const wrap = document.createElement("div");
    wrap.className = "bo-featured";

    const tabs = document.createElement("ul");
    tabs.className = "bo-cat-tabs";

    const gridWrap = document.createElement("div");
    gridWrap.className = "bo-product-grid";

    categories.forEach((cat, i) => {
      const count = getProducts(genderId, cat.id).length;
      const li = document.createElement("li");
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "bo-cat-tab" + (i === 0 ? " active" : "");
      btn.innerHTML = `${escapeHtml(cat.label)}<span class="bo-cat-count">${count}</span>`;
      btn.addEventListener("click", () => {
        tabs.querySelectorAll(".bo-cat-tab").forEach((t) => t.classList.remove("active"));
        btn.classList.add("active");
        fillGrid(genderId, cat.id);
      });
      li.appendChild(btn);
      tabs.appendChild(li);
    });

    function fillGrid(gId, catId) {
      gridWrap.innerHTML = "";
      getProducts(gId, catId).forEach((p) => gridWrap.appendChild(createProductCard(p)));
    }

    fillGrid(genderId, firstCat);
    wrap.appendChild(tabs);
    wrap.appendChild(gridWrap);
    return wrap;
  }

  function renderGenderSection(gender) {
    const section = document.createElement("section");
    section.className = "bo-gender-section";
    section.id = `section-${gender.slug}`;

    const categories = FEATURED_CATEGORIES[gender.id] || [];
    const bestSellers = getBestSellers(gender.id, 6);

    section.innerHTML = `
      <div class="bo-section-head">
        <span class="bo-eyebrow">${gender.label}</span>
        <div class="bo-section-head__row">
          <h2 class="bo-section-title"><em>Best</em> Sellers</h2>
          <a href="#" class="bo-view-all" data-gender="${gender.id}">VIEW ALL</a>
        </div>
      </div>
    `;

    const carousel = document.createElement("div");
    carousel.className = "bo-carousel";
    bestSellers.forEach((p) => carousel.appendChild(createProductCard(p)));
    section.appendChild(carousel);

    const featHead = document.createElement("div");
    featHead.className = "bo-section-head bo-section-head--spaced";
    featHead.innerHTML = `
      <span class="bo-eyebrow">${gender.label}</span>
      <h2 class="bo-section-title"><em>Featured</em> categories</h2>
    `;
    section.appendChild(featHead);
    section.appendChild(renderFeaturedGrid(gender.id, categories));

    return section;
  }

  function renderCatalog() {
    const catalogEl = document.getElementById("catalog");
    if (!catalogEl) {
      console.error("[Shop] Missing #catalog element");
      return;
    }

    if (typeof PRODUCTS === "undefined" || !Array.isArray(PRODUCTS)) {
      catalogEl.innerHTML =
        '<p class="bo-load-error">Product catalog failed to load. Hard-refresh (Ctrl+Shift+R) and confirm <code>js/products.js</code> appears in the Network tab.</p>';
      return;
    }

    if (typeof GENDERS === "undefined" || !Array.isArray(GENDERS)) {
      catalogEl.innerHTML =
        '<p class="bo-load-error">Stale catalog cache — your browser loaded an old <code>products.js</code>. Press <strong>Ctrl+Shift+R</strong> (hard refresh) to load the Breakout catalog.</p>';
      return;
    }

    catalogEl.innerHTML = "";
    GENDERS.forEach((g) => catalogEl.appendChild(renderGenderSection(g)));

    catalogEl.querySelectorAll(".bo-view-all").forEach((link) => {
      link.addEventListener("click", (e) => {
        e.preventDefault();
        const gender = link.dataset.gender;
        const slug = GENDERS.find((x) => x.id === gender)?.slug || "men";
        document.getElementById(`section-${slug}`)?.scrollIntoView({ behavior: "smooth" });
      });
    });
  }

  function boot() {
    try {
      renderCatalog();
    } catch (err) {
      console.error("[Shop] Render failed:", err);
      const catalogEl = document.getElementById("catalog");
      if (catalogEl) {
        catalogEl.innerHTML =
          '<p class="bo-load-error">Could not render products: ' + escapeHtml(err.message) + "</p>";
      }
    }

    const params = new URLSearchParams(window.location.search);
    const productId = params.get("product");
    if (productId) {
      const product = getProduct(productId);
      if (product) VTONWidget.open(product);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
