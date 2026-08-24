(function () {
  const listEl = document.getElementById("checkout-items");
  const totalEl = document.getElementById("checkout-total");
  const form = document.getElementById("checkout-form");
  const success = document.getElementById("checkout-success");
  const items = Cart.getItems();

  if (!items.length) {
    listEl.innerHTML = "<li><p>Your cart is empty. <a href='index.html'>Return to shop</a></p></li>";
    totalEl.textContent = "Total PKR 0";
    form.querySelector("button[type=submit]").disabled = true;
    return;
  }

  listEl.innerHTML = items
    .map(
      (i) => `
    <li class="bo-cart-item bo-cart-item--compact">
      <img src="${i.image}" alt="" class="bo-cart-item__img" />
      <div class="bo-cart-item__info">
        <p class="bo-cart-item__name">${i.name}</p>
        <p class="bo-cart-item__meta">${i.size} × ${i.qty} · ${formatPrice(i.price * i.qty)}</p>
      </div>
    </li>`
    )
    .join("");

  totalEl.textContent = "Total " + formatPrice(Cart.getTotal());

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    Cart.clear();
    form.hidden = true;
    document.querySelector(".checkout-summary").hidden = true;
    success.hidden = false;
  });
})();
