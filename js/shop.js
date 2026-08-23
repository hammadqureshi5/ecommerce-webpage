/**
 * Shop page logic.
 *
 * Flow:
 *   1. User picks Male or Female
 *   2. Products show in 3 groups: Shirt, Pant, Full body
 *   3. "Try on" ? go to try-on.html?product=<id>
 */

(function () {
  const catalogEl = document.getElementById("catalog");
  const genderBtns = document.querySelectorAll(".gender-btn");

  let currentGender = "male";

  // ?? Render everything ????????????????????????????????????????????????
  function render() {
    catalogEl.innerHTML = "";

    for (const cat of CATEGORIES) {
      const products = getProducts(currentGender, cat.id);
      if (!products.length) continue;

      const section = document.createElement("section");
      section.className = "category-section";

      section.innerHTML = `
        <h2 class="category-title">${cat.icon} ${cat.label}</h2>
        <div class="product-grid" id="grid-${cat.id}"></div>
      `;

      const grid = section.querySelector(".product-grid");

      for (const product of products) {
        grid.appendChild(createCard(product));
      }

      catalogEl.appendChild(section);
    }
  }

  // ?? One product card ?????????????????????????????????????????????????
  function createCard(product) {
    const card = document.createElement("article");
    card.className = "product-card";

    card.innerHTML = `
      <div class="product-image" style="background: ${product.color}">
        <span>${categoryIcon(product.category)}</span>
        <span class="garment-label">${product.garment_type}</span>
      </div>
      <div class="product-info">
        <h3>${product.name}</h3>
        <p>${product.description}</p>
        <span class="product-meta">vton_type: ${product.category}</span>
        <button class="try-on-btn" data-id="${product.id}">Try on</button>
      </div>
    `;

    card.querySelector(".try-on-btn").addEventListener("click", () => {
      // Save product id in URL so try-on page knows which garment was picked
      window.location.href = `try-on.html?product=${product.id}`;
    });

    return card;
  }

  function categoryIcon(categoryId) {
    const found = CATEGORIES.find((c) => c.id === categoryId);
    return found ? found.icon : "??";
  }

  // ?? Gender toggle ????????????????????????????????????????????????????
  genderBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      genderBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentGender = btn.dataset.gender;
      render();
    });
  });

  render();
})();
