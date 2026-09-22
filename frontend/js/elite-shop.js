/**
 * Modern Elegance — homepage product grid and navigation.
 */
(function () {
  const catalog = () => (typeof PRODUCTS !== "undefined" ? PRODUCTS : window.PRODUCTS || []);

  function escapeHtml(str) {
    const d = document.createElement("div");
    d.textContent = String(str ?? "");
    return d.innerHTML;
  }

  function categoryLine(p) {
    const catFn = typeof vtonCategoryLabel === "function" ? vtonCategoryLabel : window.vtonCategoryLabel;
    const garFn = typeof garmentTypeLabel === "function" ? garmentTypeLabel : window.garmentTypeLabel;
    const cat = catFn ? catFn(p.category) : "All Styles";
    const gar = garFn ? garFn(p.garment_type) : "Clothing";
    return `${cat} · ${gar}`;
  }

  function productCard(p, stagger) {
    const article = document.createElement("article");
    article.className = `group cursor-pointer${stagger ? " lg:mt-8" : ""}`;
    article.innerHTML = `
      <div class="relative aspect-[3/4] rounded-xl overflow-hidden bg-surface-container-low mb-6">
        <img class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105" src="${escapeHtml(p.image)}" alt="${escapeHtml(p.name)}" loading="lazy" referrerpolicy="no-referrer" />
        <div class="absolute inset-0 bg-primary/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end p-4">
          <button type="button" class="quick-add w-full bg-surface text-primary font-label-lg py-3 rounded-lg transform translate-y-4 group-hover:translate-y-0 transition-transform duration-300 hover:bg-surface-container-high">
            Quick Add — ${formatPrice(p.price)}
          </button>
        </div>
      </div>
      <div>
        <h4 class="font-label-lg text-label-lg text-primary line-clamp-2">${escapeHtml(p.name)}</h4>
        <p class="font-body-sm text-on-surface-variant mt-1">${formatPrice(p.price)}</p>
        <p class="font-label-md text-[11px] text-on-surface-variant/80 mt-2 uppercase tracking-wide">${categoryLine(p)}</p>
      </div>`;

    article.querySelector(".quick-add").addEventListener("click", (e) => {
      e.stopPropagation();
      EliteCart.add(p, { size: "M" });
      EliteCart.openDrawer();
    });
    article.addEventListener("click", () => {
      window.location.href = `product.html?id=${encodeURIComponent(p.id)}`;
    });
    return article;
  }

  function fillGrid(gridId, products) {
    const grid = document.getElementById(gridId);
    if (!grid) return;
    grid.innerHTML = "";
    if (!products.length) {
      grid.innerHTML = `<p class="col-span-full font-body-sm text-on-surface-variant py-8">No products in this category yet.</p>`;
      return;
    }
    products.forEach((p, i) => grid.appendChild(productCard(p, i % 2 === 1)));
  }

  function renderTrending() {
    const items = catalog();
    if (!items.length) {
      fillGrid("trending-grid", []);
      return;
    }
    const male = typeof getBestSellers === "function" ? getBestSellers("male", 4) : items.filter((p) => p.gender === "male").slice(0, 4);
    const female = typeof getBestSellers === "function" ? getBestSellers("female", 4) : items.filter((p) => p.gender === "female").slice(0, 4);
    fillGrid("trending-grid", [...male, ...female].slice(0, 8));
  }

  function bindSidebarToggle() {
    const toggle = document.getElementById("sidebar-toggle");
    if (!toggle) return;

    const stored = localStorage.getItem("elite-sidebar-collapsed");
    if (stored === "true") {
      document.body.classList.add("sidebar-collapsed");
      toggle.setAttribute("aria-pressed", "false");
    }

    toggle.addEventListener("click", () => {
      const collapsed = document.body.classList.toggle("sidebar-collapsed");
      localStorage.setItem("elite-sidebar-collapsed", collapsed ? "true" : "false");
      toggle.setAttribute("aria-pressed", collapsed ? "false" : "true");
    });
  }

  function bindSearch() {
    const overlay = document.getElementById("search-overlay");
    const input = document.getElementById("search-input");
    const results = document.getElementById("search-results");
    const openBtn = document.getElementById("search-btn-desktop");
    const closeBtn = document.getElementById("search-close");
    if (!overlay || !input || !results) return;

    function openSearch() {
      overlay.classList.remove("hidden");
      overlay.classList.add("flex");
      input.focus();
    }
    function closeSearch() {
      overlay.classList.add("hidden");
      overlay.classList.remove("flex");
      input.value = "";
      results.innerHTML = "";
    }

    openBtn?.addEventListener("click", openSearch);
    closeBtn?.addEventListener("click", closeSearch);
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) closeSearch();
    });

    input.addEventListener("input", () => {
      const q = input.value.trim().toLowerCase();
      if (!q) {
        results.innerHTML = "";
        return;
      }
      const matches = catalog().filter((p) => p.name.toLowerCase().includes(q)).slice(0, 8);
      results.innerHTML = matches.length
        ? matches
            .map(
              (p) =>
                `<a href="product.html?id=${encodeURIComponent(p.id)}" class="block py-3 border-b border-outline-variant/30 hover:text-primary font-body-sm">${escapeHtml(p.name)}</a>`
            )
            .join("")
        : `<p class="font-body-sm text-on-surface-variant py-3">No results found.</p>`;
    });
  }

  function bindNav() {
    const drawerBtn = document.getElementById("drawer-btn");
    const closeBtn = document.getElementById("close-drawer-btn");
    const drawer = document.getElementById("nav-drawer");
    const scrim = document.getElementById("nav-drawer-scrim");

    function openDrawer() {
      scrim?.classList.remove("hidden");
      requestAnimationFrame(() => {
        scrim?.classList.remove("opacity-0");
        drawer?.classList.remove("-translate-x-full");
      });
    }
    function closeDrawer() {
      scrim?.classList.add("opacity-0");
      drawer?.classList.add("-translate-x-full");
      setTimeout(() => scrim?.classList.add("hidden"), 300);
    }

    drawerBtn?.addEventListener("click", openDrawer);
    closeBtn?.addEventListener("click", closeDrawer);
    scrim?.addEventListener("click", closeDrawer);

    document.querySelectorAll("[data-gender-link]").forEach((a) => {
      a.addEventListener("click", (e) => {
        e.preventDefault();
        const g = a.dataset.genderLink;
        const target = document.getElementById(`section-${g}`);
        target?.scrollIntoView({ behavior: "smooth" });
        closeDrawer();
      });
    });
  }

  function renderVtonCategoryGrids() {
    const getByCat =
      typeof getProductsByVtonCategory === "function"
        ? getProductsByVtonCategory
        : (cat, limit = 8) => catalog().filter((p) => p.category === cat).slice(0, limit);
    fillGrid("grid-full-body", getByCat("full_body", 8));
    fillGrid("grid-upper-body", getByCat("upper_body", 8));
    fillGrid("grid-lower-body", getByCat("lower_body", 8));
  }

  function renderGenderSections() {
    fillGrid("grid-female", catalog().filter((p) => p.gender === "female").slice(0, 8));
    fillGrid("grid-male", catalog().filter((p) => p.gender === "male").slice(0, 8));
  }

  function showLoadError(msg) {
    const main = document.querySelector("main");
    if (!main || document.getElementById("catalog-error")) return;
    const el = document.createElement("div");
    el.id = "catalog-error";
    el.className = "mx-4 lg:mx-12 mb-8 p-4 bg-error-container text-on-error-container rounded-lg font-body-sm";
    el.textContent = msg;
    main.prepend(el);
  }

  function init() {
    try {
      const items = catalog();
      if (!items.length) {
        showLoadError("Product catalog failed to load. Hard-refresh the page (Ctrl+Shift+R) or run: cd frontend && python -m http.server 5500");
        return;
      }
      renderTrending();
      renderVtonCategoryGrids();
      renderGenderSections();

      const params = new URLSearchParams(location.search);
      const productId = params.get("product");
      if (productId) {
        const p = typeof getProduct === "function" ? getProduct(productId) : items.find((x) => x.id === productId);
        if (p) EliteVTON.open(p);
      }
    } catch (err) {
      console.error("[EliteShop]", err);
      showLoadError("Could not render products: " + (err.message || "unknown error"));
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    bindNav();
    bindSidebarToggle();
    bindSearch();
    init();
  });
})();
