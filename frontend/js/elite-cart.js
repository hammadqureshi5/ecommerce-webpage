/**
 * Cart for Modern Elegance storefront — localStorage + Stitch-styled drawer.
 */
const EliteCart = (function () {
  const STORAGE_KEY = "elite-cart-v1";
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
    if (existing) existing.qty += 1;
    else {
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

  function escapeHtml(str) {
    const d = document.createElement("div");
    d.textContent = str;
    return d.innerHTML;
  }

  function openDrawer() {
    const drawer = document.getElementById("cart-drawer");
    const scrim = document.getElementById("cart-scrim");
    if (!drawer || !scrim) return;
    scrim.classList.remove("hidden");
    requestAnimationFrame(() => {
      scrim.classList.remove("opacity-0");
      drawer.classList.remove("translate-x-full");
    });
  }

  function closeDrawer() {
    const drawer = document.getElementById("cart-drawer");
    const scrim = document.getElementById("cart-scrim");
    if (!drawer || !scrim) return;
    scrim.classList.add("opacity-0");
    drawer.classList.add("translate-x-full");
    setTimeout(() => scrim.classList.add("hidden"), 300);
  }

  function render() {
    const count = getCount();
    document.querySelectorAll("[data-cart-count]").forEach((el) => {
      el.textContent = count;
    });
    document.querySelectorAll("[data-cart-dot]").forEach((el) => {
      el.classList.toggle("hidden", count === 0);
    });

    const body = document.getElementById("cart-body");
    if (!body) return;

    if (!items.length) {
      body.innerHTML = `
        <div class="text-center py-12 px-4">
          <p class="font-body-md text-on-surface-variant mb-2">Your bag is empty.</p>
          <button type="button" data-close-cart class="font-label-lg text-primary border-b border-primary mt-4">Continue shopping</button>
        </div>`;
      body.querySelector("[data-close-cart]")?.addEventListener("click", closeDrawer);
      return;
    }

    const total = getTotal();
    body.innerHTML = `
      <ul class="flex flex-col gap-4 mb-6">
        ${items
          .map(
            (i) => `
          <li class="flex gap-4 border-b border-outline-variant/30 pb-4" data-key="${i.key}">
            <img src="${i.image}" alt="" class="w-20 h-24 object-cover rounded-lg bg-surface-container" referrerpolicy="no-referrer" />
            <div class="flex-1 min-w-0">
              <p class="font-label-lg text-label-lg text-primary truncate">${escapeHtml(i.name)}</p>
              <p class="font-body-sm text-on-surface-variant mt-1">Size ${i.size} · ${formatPrice(i.price)}</p>
              <div class="flex items-center gap-3 mt-2">
                <button type="button" data-action="dec" class="w-8 h-8 border border-outline-variant rounded text-primary">−</button>
                <span class="font-body-sm">${i.qty}</span>
                <button type="button" data-action="inc" class="w-8 h-8 border border-outline-variant rounded text-primary">+</button>
              </div>
            </div>
            <button type="button" data-remove class="text-on-surface-variant hover:text-primary text-xl">&times;</button>
          </li>`
          )
          .join("")}
      </ul>
      <div class="border-t border-outline-variant pt-4 space-y-3">
        <p class="font-label-lg text-primary flex justify-between"><span>Total</span><span>${formatPrice(total)}</span></p>
        <a href="checkout.html" class="block w-full text-center bg-primary text-on-primary font-label-lg py-3 rounded-lg hover:bg-primary-container transition-colors">Checkout</a>
        <button type="button" data-close-cart class="block w-full border border-outline font-label-lg py-3 rounded-lg text-on-surface hover:bg-surface-container transition-colors">Continue shopping</button>
      </div>`;

    body.querySelectorAll("li[data-key]").forEach((row) => {
      const key = row.dataset.key;
      row.querySelector("[data-remove]").addEventListener("click", () => remove(key));
      row.querySelector('[data-action="dec"]').addEventListener("click", () => {
        const item = items.find((x) => x.key === key);
        if (item) setQty(key, item.qty - 1);
      });
      row.querySelector('[data-action="inc"]').addEventListener("click", () => {
        const item = items.find((x) => x.key === key);
        if (item) setQty(key, item.qty + 1);
      });
    });
    body.querySelector("[data-close-cart]")?.addEventListener("click", closeDrawer);
  }

  function bindUi() {
    document.querySelectorAll("[data-open-cart]").forEach((btn) => {
      btn.addEventListener("click", openDrawer);
    });
    document.querySelectorAll("[data-close-cart]").forEach((btn) => {
      btn.addEventListener("click", closeDrawer);
    });
    document.getElementById("cart-scrim")?.addEventListener("click", closeDrawer);
  }

  render();
  document.addEventListener("DOMContentLoaded", bindUi);

  function getItems() {
    return items.map((i) => ({ ...i }));
  }

  function clear() {
    items = [];
    save();
  }

  return { add, remove, setQty, getCount, getTotal, getItems, clear, openDrawer, closeDrawer, render };
})();
