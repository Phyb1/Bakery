/**
 * cart.js
 *
 * Minimal, dependency-free cart for the "digital menu + WhatsApp order"
 * model: no server-side cart, no payment gateway. Everything lives in
 * localStorage until checkout, at which point it's turned into a single
 * pre-filled WhatsApp message.
 *
 * Kept intentionally small (~3KB unminified) for 2G/3G Zimbabwean
 * networks - no build step, no framework.
 *
 * Public functions used by templates (product_card.html, base.html):
 *   addToCart(id, name, price)
 *   changeQty(id, delta)
 *   removeFromCart(id)
 *   openCart() / closeCart()
 *   checkoutWhatsApp(whatsappNumberDigitsOnly)
 */

const CART_STORAGE_KEY = "samwa_cart";

/** @returns {Array<{id:string, name:string, price:number, qty:number}>} */
function getCart() {
  try {
    return JSON.parse(localStorage.getItem(CART_STORAGE_KEY)) || [];
  } catch (e) {
    // Corrupt localStorage shouldn't crash the page - just start fresh.
    return [];
  }
}

function saveCart(cart) {
  localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cart));
  renderCartCount();
  renderCartItems();
}

/**
 * Add `qty` units of a product to the cart (default 1), incrementing if
 * it's already there. Called from the "Add to cart" button on product
 * cards, using whatever quantity is currently shown in that card's
 * picker (see adjustPickerQty below).
 */
function addToCart(id, name, price, qty = 1) {
  const cart = getCart();
  const existing = cart.find((item) => item.id === id);
  if (existing) {
    existing.qty += qty;
  } else {
    cart.push({ id, name, price: parseFloat(price), qty });
  }
  saveCart(cart);
}

/**
 * v2.1 quantity picker: adjusts the number shown on a product card
 * *before* it's added to the cart. This is intentionally separate from
 * changeQty() below, which edits quantities of items already in the
 * cart - conflating the two would mean clicking "+" on one product's
 * picker could accidentally change a different item sitting in the cart.
 * Never lets the on-card quantity go below 1.
 */
function adjustPickerQty(id, delta) {
  const el = document.getElementById(`qty-${id}`);
  if (!el) return;
  const next = Math.max(1, parseInt(el.textContent, 10) + delta);
  el.textContent = next;
}

function getPickerQty(id) {
  const el = document.getElementById(`qty-${id}`);
  return el ? Math.max(1, parseInt(el.textContent, 10)) : 1;
}

/**
 * Increase/decrease quantity for an item already in the cart.
 * Removes the item entirely if qty drops to 0.
 */
function changeQty(id, delta) {
  const cart = getCart();
  const item = cart.find((i) => i.id === id);
  if (!item) return;
  item.qty += delta;
  const updated = item.qty > 0 ? cart : cart.filter((i) => i.id !== id);
  saveCart(updated);
}

function removeFromCart(id) {
  saveCart(getCart().filter((i) => i.id !== id));
}

function cartTotal(cart) {
  return cart.reduce((sum, item) => sum + item.price * item.qty, 0);
}

function cartCount(cart) {
  return cart.reduce((sum, item) => sum + item.qty, 0);
}

/** Updates the small badge in the header, e.g. "Cart (3)". */
function renderCartCount() {
  const el = document.getElementById("cart-count");
  if (el) el.textContent = cartCount(getCart());
}

/** Renders the line items + total inside the cart modal. */
function renderCartItems() {
  const container = document.getElementById("cart-items");
  if (!container) return;

  const cart = getCart();

  if (cart.length === 0) {
    container.innerHTML = '<p class="cart-empty">Your cart is empty.</p>';
    return;
  }

  const lines = cart
    .map((item) => {
      const lineTotal = (item.price * item.qty).toFixed(2);
      return `
        <div class="cart-line">
          <span>${item.qty}x ${escapeHtml(item.name)}</span>
          <span>$${lineTotal}</span>
        </div>`;
    })
    .join("");

  const totalHtml = `<div class="cart-total">Total: $${cartTotal(cart).toFixed(2)}</div>`;

  container.innerHTML = lines + totalHtml;
}

/** Basic HTML-escaping so product names can't break the cart markup. */
function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function openCart() {
  const modal = document.getElementById("cart-modal");
  if (modal) modal.classList.add("open");
  renderCartItems();
}

function closeCart() {
  const modal = document.getElementById("cart-modal");
  if (modal) modal.classList.remove("open");
}

/**
 * Build a single WhatsApp message summarising every item in the cart and
 * open wa.me with it pre-filled. Clears the cart afterwards, assuming the
 * customer is about to send the order.
 *
 * @param {string} whatsappNumber - digits only (no '+'), e.g. from
 *   {{ bakery.clean_whatsapp }} in the template.
 */
function checkoutWhatsApp(whatsappNumber) {
  const cart = getCart();
  if (cart.length === 0) {
    alert("Your cart is empty. Add something from the menu first.");
    return;
  }

  let message = "Hi! I'd like to order:\n\n";
  cart.forEach((item) => {
    const lineTotal = (item.price * item.qty).toFixed(2);
    message += `${item.qty}x ${item.name} = $${lineTotal}\n`;
  });
  message += `\nTotal: $${cartTotal(cart).toFixed(2)}`;

  const url = `https://wa.me/${whatsappNumber}?text=${encodeURIComponent(message)}`;
  window.open(url, "_blank");

  localStorage.removeItem(CART_STORAGE_KEY);
  renderCartCount();
  renderCartItems();
  closeCart();
}

// Populate the cart badge as soon as the script loads (e.g. after a
// page reload with items already in localStorage from a previous visit).
document.addEventListener("DOMContentLoaded", renderCartCount);
