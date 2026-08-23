/**
 * Outfit store — browse products, open VTON widget on "Try on".
 */

(function () {
  const catalogEl = document.getElementById("catalog");
  const genderBtns = document.querySelectorAll(".gender-btn");

  let currentGender = "male";

  function render() {
    catalogEl.innerHTML = "";

    for (const cat of STORE_CATEGORIES) {
      const products = getProducts(currentGender, cat.id);
      if (!products.length) continue;

      const section = document.createElement("section");
      section.className = "category-section";

      section.innerHTML = `
        <h2 class="category-title">${cat.label}</h2>
        <div class="product-grid"></div>
      `;

      const grid = section.querySelector(".product-grid");
      for (const product of products) {
        grid.appendChild(createCard(product));
      }

      catalogEl.appendChild(section);
    }
  }

  function createCard(product) {
    const card = document.createElement("article");
    card.className = "product-card";

    card.innerHTML = `
      <div class="product-image">
        <img src="${product.image}" alt="${product.name}" loading="lazy"
             onerror="this.style.display='none'; this.parentElement.style.background='${product.color}'" />
      </div>
      <div class="product-info">
        <h3>${product.name}</h3>
        <p>${product.description}</p>
        <span class="product-price">${formatPrice(product.price)}</span>
        <div class="product-actions">
          <button type="button" class="btn-secondary">Add to cart</button>
          <button type="button" class="btn-try-on">Try on</button>
        </div>
      </div>
    `;

    card.querySelector(".btn-try-on").addEventListener("click", () => {
      VTONWidget.open(product);
    });

    card.querySelector(".btn-secondary").addEventListener("click", () => {
      alert("Cart is not implemented in this demo.");
    });

    return card;
  }

  genderBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      genderBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentGender = btn.dataset.gender;
      render();
    });
  });

  render();

  // Support old links: try-on.html?product=... → open widget on load
  const params = new URLSearchParams(window.location.search);
  const productId = params.get("product");
  if (productId) {
    const product = getProduct(productId);
    if (product) VTONWidget.open(product);
  }
})();
