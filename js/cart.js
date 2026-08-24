/**
 * Shopping cart — localStorage, drawer UI, checkout handoff.
 */
const Cart = (function () {
  const STORAGE_KEY = "breakout-cart-v1";
  let items = load();

  function load() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    } catch {
      return [];
    }
  }

  function save() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
    render();
    window.dispatchEvent(new CustomEvent("cart:updated", { detail: { items, total: getTotal() } }));
  }

  function getItems() {
    return items.slice();
  }

  function getCount() {
    return items.reduce((n, i) => n + i.qty, 0);
  }

  function getTotal() {
    return items.reduce((sum, i) => sum + i.price * i.qty, 0);
  }

  function add(product, opts = {}) {
    const size = opts.size || "M";
    const key = product.id + "::" + size;
    const existing = items.find((i) => i.key === key);
    if (existing) {
      existing.qty += 1;
    } else {
      items.push({
        key,
        id: product.id,
        name: product.name,
        image: product.image,
        price: product.price,
        size,
        qty: 1,
      });
    }
    save();
  }

  function remove(key) {
    items = items.filter((i) => i.key !== key);
    save();
  }

  function setQty(key, qty) {
    const item = items.find((i) => i.key === key);
    if (!item) return;
    if (qty <= 0) remove(key);
    else {
      item.qty = qty;
      save();
    }
  }

  function clear() {
    items = [];
    save();
  }

  function render() {
    const count = getCount();
    const total = getTotal();
    document.querySelectorAll("#cart-count, #cart-count-drawer").forEach((el) => {
      if (el) el.textContent = count;
    });

    const body = document.getElementById("cart-body");
    if (!body) return;

    if (!items.length) {
      body.innerHTML = `
        <div class="bo-cart-empty">
          <p>Your cart is currently empty.</p>
          <p class="bo-cart-total">0 PKR 0</p>
          <button type="button" class="bo-btn bo-btn--outline" data-close-drawer>Continue shopping</button>
        </div>
      `;
      body.querySelector("[data-close-drawer]")?.addEventListener("click", () => {
        document.querySelector("#drawer-cart [data-close-drawer]")?.click();
      });
      return;
    }

    body.innerHTML = `
      <ul class="bo-cart-list">
        ${items
          .map(
            (i) => `
          <li class="bo-cart-item" data-key="${i.key}">
            <img src="${i.image}" alt="" class="bo-cart-item__img" />
            <div class="bo-cart-item__info">
              <p class="bo-cart-item__name">${escapeHtml(i.name)}</p>
              <p class="bo-cart-item__meta">Size: ${i.size} · ${formatPrice(i.price)}</p>
              <div class="bo-cart-item__qty">
                <button type="button" class="bo-qty-btn" data-action="dec" aria-label="Decrease">−</button>
                <span>${i.qty}</span>
                <button type="button" class="bo-qty-btn" data-action="inc" aria-label="Increase">+</button>
              </div>
            </div>
            <button type="button" class="bo-cart-item__remove" aria-label="Remove">&times;</button>
          </li>`
          )
          .join("")}
      </ul>
      <div class="bo-cart-summary">
        <p class="bo-cart-total">Total ${formatPrice(total)}</p>
        <p class="bo-cart-note">Taxes and shipping calculated at checkout</p>
        <a href="checkout.html" class="bo-btn bo-btn--full">Checkout</a>
        <button type="button" class="bo-btn bo-btn--outline bo-btn--full" data-close-drawer>Continue shopping</button>
      </div>
    `;

    body.querySelectorAll(".bo-cart-item").forEach((row) => {
      const key = row.dataset.key;
      row.querySelector(".bo-cart-item__remove").addEventListener("click", () => remove(key));
      row.querySelector('[data-action="dec"]').addEventListener("click", () => {
        const item = items.find((x) => x.key === key);
        if (item) setQty(key, item.qty - 1);
      });
      row.querySelector('[data-action="inc"]').addEventListener("click", () => {
        const item = items.find((x) => x.key === key);
        if (item) setQty(key, item.qty + 1);
      });
    });

    body.querySelector("[data-close-drawer]")?.addEventListener("click", () => {
      document.querySelector("#drawer-cart .bo-drawer__close")?.click();
    });
  }

  function escapeHtml(str) {
    const d = document.createElement("div");
    d.textContent = str;
    return d.innerHTML;
  }

  render();
  return { add, remove, setQty, clear, getItems, getCount, getTotal, render };
})();
