/**
 * Product options modal — Choose options → size + Add to cart / Try on.
 */
const ProductModal = (function () {
  let overlay = null;
  let product = null;
  const SIZES = ["XS", "S", "M", "L", "XL", "XXL"];

  function ensureDom() {
    if (overlay) return;
    overlay = document.createElement("div");
    overlay.className = "bo-product-modal";
    overlay.id = "product-modal";
    overlay.innerHTML = `
      <div class="bo-product-modal__backdrop" data-close></div>
      <div class="bo-product-modal__dialog" role="dialog" aria-modal="true">
        <button type="button" class="bo-product-modal__close" data-close aria-label="Close">&times;</button>
        <div class="bo-product-modal__grid">
          <div class="bo-product-modal__media">
            <img id="pm-image" src="" alt="" />
          </div>
          <div class="bo-product-modal__details">
            <h2 id="pm-title"></h2>
            <div id="pm-price" class="bo-product-modal__price"></div>
            <p class="bo-product-modal__label">Size</p>
            <div class="bo-size-picker" id="pm-sizes"></div>
            <button type="button" class="bo-btn bo-btn--full" id="pm-add-cart">Add to cart</button>
            <button type="button" class="bo-btn bo-btn--outline bo-btn--full" id="pm-try-on">Virtual try-on</button>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);

    overlay.querySelectorAll("[data-close]").forEach((el) => {
      el.addEventListener("click", close);
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && overlay.classList.contains("open")) close();
    });

    overlay.querySelector("#pm-add-cart").addEventListener("click", () => {
      if (!product) return;
      const size = overlay.querySelector(".bo-size-btn.active")?.dataset.size || "M";
      Cart.add(product, { size });
      close();
      document.getElementById("btn-cart")?.click();
    });

    overlay.querySelector("#pm-try-on").addEventListener("click", () => {
      if (!product) return;
      close();
      VTONWidget.open(product);
    });
  }

  function open(p) {
    ensureDom();
    product = p;
    overlay.querySelector("#pm-image").src = p.image;
    overlay.querySelector("#pm-image").alt = p.name;
    overlay.querySelector("#pm-title").textContent = p.name;
    overlay.querySelector("#pm-price").innerHTML = formatPriceHtml(p);

    const sizesEl = overlay.querySelector("#pm-sizes");
    sizesEl.innerHTML = SIZES.map(
      (s, i) =>
        `<button type="button" class="bo-size-btn${i === 2 ? " active" : ""}" data-size="${s}">${s}</button>`
    ).join("");
    sizesEl.querySelectorAll(".bo-size-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        sizesEl.querySelectorAll(".bo-size-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
      });
    });

    overlay.classList.add("open");
    document.body.classList.add("bo-modal-open");
  }

  function close() {
    if (!overlay) return;
    overlay.classList.remove("open");
    document.body.classList.remove("bo-modal-open");
    product = null;
  }

  return { open, close };
})();
