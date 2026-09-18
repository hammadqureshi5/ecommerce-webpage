/**
 * Checkout page for Modern Elegance — renders the bag, fakes an order.
 */
(function () {
  const listEl = document.getElementById("checkout-items");
  const totalEl = document.getElementById("checkout-total");
  const form = document.getElementById("checkout-form");
  const summary = document.getElementById("checkout-summary");
  const success = document.getElementById("checkout-success");
  const items = EliteCart.getItems();

  if (!items.length) {
    listEl.innerHTML = `
      <li class="py-8 text-center">
        <p class="font-body-md text-on-surface-variant mb-4">Your bag is empty.</p>
        <a href="index.html" class="font-label-lg text-primary border-b border-primary">Return to shop</a>
      </li>`;
    totalEl.textContent = formatPrice(0);
    form.querySelector("button[type=submit]").disabled = true;
    form.querySelector("button[type=submit]").classList.add("opacity-40", "cursor-not-allowed");
    return;
  }

  listEl.innerHTML = items
    .map(
      (i) => `
      <li class="flex gap-4 border-b border-outline-variant/30 pb-4">
        <img src="${i.image}" alt="" class="w-20 h-24 object-cover rounded-lg bg-surface-container" referrerpolicy="no-referrer" />
        <div class="flex-1 min-w-0">
          <p class="font-label-lg text-label-lg text-primary truncate">${i.name}</p>
          <p class="font-body-sm text-on-surface-variant mt-1">Size ${i.size} × ${i.qty}</p>
        </div>
        <p class="font-body-sm text-primary whitespace-nowrap">${formatPrice(i.price * i.qty)}</p>
      </li>`
    )
    .join("");

  totalEl.textContent = formatPrice(EliteCart.getTotal());

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    EliteCart.clear();
    form.hidden = true;
    summary.hidden = true;
    success.hidden = false;
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
})();
