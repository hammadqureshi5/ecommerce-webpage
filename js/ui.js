/**
 * Breakout UI — mega menu, drawers, search, sticky header.
 */

(function () {
  function boot() {
  const header = document.getElementById("bo-header");
  const drawerMenu = document.getElementById("drawer-menu");
  const drawerSearch = document.getElementById("drawer-search");
  const drawerCart = document.getElementById("drawer-cart");
  const mobileNav = document.getElementById("mobile-nav");
  const searchInput = document.getElementById("search-input");
  const searchHints = document.getElementById("search-hints");
  const searchResults = document.getElementById("search-results");

  let megaPanel = null;

  function openDrawer(drawer) {
    document.body.classList.add("bo-drawer-open");
    drawer.classList.add("open");
    drawer.setAttribute("aria-hidden", "false");
  }

  function closeDrawers() {
    document.body.classList.remove("bo-drawer-open");
    [drawerMenu, drawerSearch, drawerCart].forEach((d) => {
      d?.classList.remove("open");
      d?.setAttribute("aria-hidden", "true");
    });
    hideMega();
  }

  document.getElementById("btn-menu")?.addEventListener("click", () => openDrawer(drawerMenu));
  document.getElementById("btn-search")?.addEventListener("click", () => {
    openDrawer(drawerSearch);
    setTimeout(() => searchInput?.focus(), 200);
  });
  document.getElementById("btn-cart")?.addEventListener("click", () => {
    if (typeof Cart !== "undefined") Cart.render();
    openDrawer(drawerCart);
  });

  document.querySelectorAll("[data-close-drawer]").forEach((el) => {
    el.addEventListener("click", closeDrawers);
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeDrawers();
  });

  window.addEventListener(
    "scroll",
    () => header?.classList.toggle("is-scrolled", window.scrollY > 10),
    { passive: true }
  );

  /* ── Desktop mega menu ───────────────────────────────────────────── */

  function buildMegaPanel() {
    if (megaPanel) return;
    megaPanel = document.createElement("div");
    megaPanel.className = "bo-mega";
    megaPanel.id = "bo-mega";
    megaPanel.hidden = true;
    megaPanel.innerHTML = `<div class="bo-mega__inner" id="bo-mega-inner"></div>`;
    header.appendChild(megaPanel);
    header.addEventListener("mouseleave", hideMega);
  }

  function renderMega(genderId) {
    buildMegaPanel();
    const menu = MEGA_MENU[genderId];
    const gender = GENDERS.find((g) => g.id === genderId);
    if (!menu || !gender) return;

    megaPanel.querySelector("#bo-mega-inner").innerHTML = `
      <div class="bo-mega__col">
        <p class="bo-mega__heading">${gender.label}</p>
        ${menu.highlights.map((h) => `<a href="#section-${gender.slug}" class="bo-mega__highlight">${h}</a>`).join("")}
      </div>
      <div class="bo-mega__col">
        <p class="bo-mega__label">Clothing</p>
        <ul>${menu.clothing.map((c) => `<li><a href="#section-${gender.slug}">${c}</a></li>`).join("")}</ul>
      </div>
      <div class="bo-mega__col">
        <p class="bo-mega__label">Accessories</p>
        <ul>${menu.accessories.map((c) => `<li><a href="#section-${gender.slug}">${c}</a></li>`).join("")}</ul>
      </div>
      <div class="bo-mega__col">
        <p class="bo-mega__label">Collections</p>
        <ul>${menu.collections.map((c) => `<li><a href="#section-${gender.slug}">${c}</a></li>`).join("")}</ul>
      </div>
    `;

    megaPanel.querySelectorAll("a").forEach((a) => {
      a.addEventListener("click", (e) => {
        const href = a.getAttribute("href");
        if (href?.startsWith("#")) {
          e.preventDefault();
          hideMega();
          document.querySelector(href)?.scrollIntoView({ behavior: "smooth" });
        }
      });
    });
  }

  function showMega(genderId) {
    renderMega(genderId);
    megaPanel.hidden = false;
    megaPanel.classList.add("open");
  }

  function hideMega() {
    if (!megaPanel) return;
    megaPanel.classList.remove("open");
    megaPanel.hidden = true;
  }

  document.querySelectorAll(".bo-nav__item").forEach((item) => {
    const genderId = item.dataset.gender;
    item.addEventListener("mouseenter", () => showMega(genderId));
    item.addEventListener("focusin", () => showMega(genderId));
  });

  buildMegaPanel();

  /* ── Mobile accordion menu ───────────────────────────────────────── */

  function buildMobileNav() {
    if (!mobileNav || typeof MEGA_MENU === "undefined") return;
    mobileNav.innerHTML = GENDERS.map((g) => {
      const menu = MEGA_MENU[g.id];
      return `
        <div class="bo-mobile-group">
          <button type="button" class="bo-mobile-group__toggle" aria-expanded="false">
            ${g.nav} <span class="bo-mobile-group__icon">+</span>
          </button>
          <div class="bo-mobile-group__panel" hidden>
            ${menu.highlights.map((h) => `<a href="#section-${g.slug}" class="bo-drawer__link bo-drawer__link--hi">${h}</a>`).join("")}
            <p class="bo-mobile-label">Clothing</p>
            ${menu.clothing.map((c) => `<a href="#section-${g.slug}" class="bo-drawer__link bo-drawer__link--sub">${c}</a>`).join("")}
            <p class="bo-mobile-label">Accessories</p>
            ${menu.accessories.map((c) => `<a href="#section-${g.slug}" class="bo-drawer__link bo-drawer__link--sub">${c}</a>`).join("")}
            <p class="bo-mobile-label">Collections</p>
            ${menu.collections.map((c) => `<a href="#section-${g.slug}" class="bo-drawer__link bo-drawer__link--sub">${c}</a>`).join("")}
          </div>
        </div>
      `;
    }).join("");

    mobileNav.querySelectorAll(".bo-mobile-group__toggle").forEach((btn) => {
      btn.addEventListener("click", () => {
        const panel = btn.nextElementSibling;
        const open = btn.getAttribute("aria-expanded") === "true";
        btn.setAttribute("aria-expanded", String(!open));
        btn.querySelector(".bo-mobile-group__icon").textContent = open ? "+" : "−";
        panel.hidden = open;
      });
    });

    mobileNav.querySelectorAll("a").forEach((a) => {
      a.addEventListener("click", closeDrawers);
    });
  }

  buildMobileNav();

  /* ── Search ────────────────────────────────────────────────────── */

  function runSearch(q) {
    if (!searchResults) return;
    const query = q.trim().toLowerCase();
    if (!query) {
      searchResults.innerHTML = "";
      return;
    }
    const hits = PRODUCTS.filter((p) => p.name.toLowerCase().includes(query)).slice(0, 12);
    searchResults.innerHTML = hits.length
      ? hits
          .map(
            (p) =>
              `<button type="button" class="bo-search-result" data-id="${p.id}">
                <img src="${p.image}" alt="" /><span>${p.name}</span>
              </button>`
          )
          .join("")
      : "<p class='bo-search-empty'>No products found.</p>";

    searchResults.querySelectorAll(".bo-search-result").forEach((btn) => {
      btn.addEventListener("click", () => {
        const p = getProduct(btn.dataset.id);
        if (p) {
          closeDrawers();
          ProductModal.open(p);
        }
      });
    });
  }

  searchInput?.addEventListener("input", () => runSearch(searchInput.value));

  if (searchHints) {
    const terms = ["Tees", "Shirts", "Jeans", "Denim", "Trousers", "Co-ords"];
    searchHints.innerHTML =
      "<p class='bo-search-label'>Popular</p>" +
      terms.map((t) => `<button type="button" class="bo-search-tag">${t}</button>`).join("");
    searchHints.querySelectorAll(".bo-search-tag").forEach((btn) => {
      btn.addEventListener("click", () => {
        if (searchInput) {
          searchInput.value = btn.textContent;
          runSearch(searchInput.value);
        }
      });
    });
  }

  document.querySelectorAll(".bo-nav__link").forEach((link) => {
    link.addEventListener("click", (e) => {
      const href = link.getAttribute("href");
      if (href?.startsWith("#")) {
        e.preventDefault();
        hideMega();
        document.querySelector(href)?.scrollIntoView({ behavior: "smooth" });
      }
    });
  });
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
