/**
 * Front-end catalog logic for CAPS VNZLA.
 *
 * This module handles product rendering, category filtering, live search,
 * USD/BS conversion and the cart behavior in a single place.
 */

const productData = Array.isArray(window.catalogData) ? window.catalogData : [];
const cartStorageKey = "caps_vnzla_cart";
const state = {
  currency: localStorage.getItem("caps_vnzla_currency") || "USD",
  rate: Number(window.currencyRate || 35),
  cart: loadCart(),
  activeCategory: "all",
};

/**
 * Load saved cart data from localStorage.
 *
 * @returns {Array<{id: number, name: string, price_usd: number, quantity: number}>}
 */
function loadCart() {
  try {
    const raw = localStorage.getItem(cartStorageKey);
    return raw ? JSON.parse(raw) : [];
  } catch (error) {
    console.warn("Cart could not be loaded from localStorage:", error);
    return [];
  }
}

/**
 * Persist cart state so the order remains between sessions.
 */
function saveCart() {
  localStorage.setItem(cartStorageKey, JSON.stringify(state.cart));
}

/**
 * Format a numeric value for the active currency.
 *
 * @param {number} value - raw value in USD.
 * @param {string} currency - target currency, either USD or BS.
 * @returns {string}
 */
function formatMoney(value, currency = state.currency) {
  const numericValue = Number(value || 0);

  if (currency === "BS") {
    return `Bs ${numericValue * state.rate}`.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }

  return `$ ${numericValue.toFixed(2)}`;
}

/**
 * Convert a USD price into the selected currency.
 *
 * @param {number} priceUsd - product price in USD.
 * @returns {number}
 */
function convertPrice(priceUsd) {
  return state.currency === "BS" ? Number(priceUsd) * state.rate : Number(priceUsd);
}

/**
 * Update the visible currency label and render the cart again.
 */
function updateCurrencyUI() {
  const buttons = document.querySelectorAll(".currency-btn");
  buttons.forEach((button) => {
    const isActive = button.dataset.currency === state.currency;
    button.classList.toggle("active", isActive);
  });

  localStorage.setItem("caps_vnzla_currency", state.currency);
  updateCartDisplay();
  renderProducts(getVisibleProducts());
}

/**
 * Return products filtered by category and search term.
 *
 * @returns {Array<Object>}
 */
function getVisibleProducts() {
  const searchInput = document.getElementById("catalog-search");
  const query = searchInput ? searchInput.value.trim().toLowerCase() : "";

  return productData.filter((product) => {
    const matchesCategory =
      state.activeCategory === "all" || product.categoria_id === Number(state.activeCategory);
    const matchesSearch =
      !query || product.nombre.toLowerCase().includes(query) || product.descripcion.toLowerCase().includes(query);

    return matchesCategory && matchesSearch;
  });
}

/**
 * Render the product list in the main catalog grid.
 *
 * @param {Array<Object>} products - product list to display.
 */
function renderProducts(products) {
  const container = document.getElementById("product-grid");
  if (!container) {
    return;
  }

  if (!products.length) {
    container.innerHTML = `
      <article class="empty-state">
        <h3>No encontramos productos.</h3>
        <p>Prueba otra búsqueda o cambia la categoría seleccionada.</p>
      </article>
    `;
    return;
  }

  container.innerHTML = products
    .map(
      (product) => `
        <article class="product-card">
          <div class="product-card__media">
            <img src="${product.imagen || "/static/img/placeholder.svg"}" alt="${product.nombre}" />
            <span class="badge badge--primary">NUEVO</span>
          </div>
          <div class="product-card__body">
            <p class="product-card__category">${product.categoria}</p>
            <h3>${product.nombre}</h3>
            <p class="product-card__description">${product.descripcion.slice(0, 80)}...</p>
            <div class="product-card__meta">
              <span class="product-card__price">${formatMoney(convertPrice(product.precio_usd))}</span>
              <span class="product-card__stock">${product.stock} disponibles</span>
            </div>
            <div class="product-card__actions">
              <a href="/producto/${product.id}" class="secondary-button">Ver detalle</a>
              <button type="button" class="cta-button" data-add-to-cart="${product.id}">Añadir</button>
            </div>
          </div>
        </article>
      `,
    )
    .join("");
}

/**
 * Add a product to the cart or increment its quantity if it already exists.
 *
 * @param {number} productId - product identifier.
 */
function addToCart(productId) {
  const product = productData.find((item) => Number(item.id) === Number(productId));
  if (!product) {
    return;
  }

  const existingItem = state.cart.find((item) => Number(item.id) === Number(product.id));

  if (existingItem) {
    existingItem.quantity += 1;
  } else {
    state.cart.push({
      id: Number(product.id),
      name: product.nombre,
      price_usd: Number(product.precio_usd),
      quantity: 1,
    });
  }

  saveCart();
  updateCartDisplay();
}

/**
 * Remove or decrement an item in the cart.
 *
 * @param {number} productId - product identifier.
 * @param {string} action - action to perform: increase or decrease.
 */
function adjustCartItem(productId, action) {
  const item = state.cart.find((entry) => Number(entry.id) === Number(productId));
  if (!item) {
    return;
  }

  if (action === "increase") {
    item.quantity += 1;
  } else {
    item.quantity -= 1;
    if (item.quantity <= 0) {
      state.cart = state.cart.filter((entry) => Number(entry.id) !== Number(productId));
    }
  }

  saveCart();
  updateCartDisplay();
}

/**
 * Update the cart panel totals and rendered items.
 */
function updateCartDisplay() {
  const cartItems = document.getElementById("cart-items");
  const cartCount = document.getElementById("cart-count");
  const subtotalDisplay = document.getElementById("subtotal-display");
  const totalDisplay = document.getElementById("total-display");

  if (!cartItems || !cartCount || !subtotalDisplay || !totalDisplay) {
    return;
  }

  cartCount.textContent = String(state.cart.reduce((sum, item) => sum + item.quantity, 0));

  if (!state.cart.length) {
    cartItems.innerHTML = '<p class="empty-cart">Tu carrito está vacío.</p>';
    subtotalDisplay.textContent = formatMoney(0);
    totalDisplay.textContent = formatMoney(0);
    return;
  }

  const subtotal = state.cart.reduce(
    (sum, item) => sum + Number(item.price_usd) * item.quantity,
    0,
  );

  cartItems.innerHTML = state.cart
    .map(
      (item) => `
        <div class="cart-item">
          <div class="cart-item__info">
            <strong>${item.name}</strong>
            <span>${formatMoney(convertPrice(item.price_usd))}</span>
          </div>
          <div class="cart-item__controls">
            <button type="button" data-cart-action="decrease" data-product-id="${item.id}">-</button>
            <span>${item.quantity}</span>
            <button type="button" data-cart-action="increase" data-product-id="${item.id}">+</button>
          </div>
        </div>
      `,
    )
    .join("");

  const displaySubtotal = convertPrice(subtotal);
  subtotalDisplay.textContent = formatMoney(displaySubtotal);
  totalDisplay.textContent = formatMoney(displaySubtotal);
}

/**
 * Attach event listeners to the UI after the DOM loads.
 */
function bindEvents() {
  const searchInput = document.getElementById("catalog-search");
  const filterButtons = document.querySelectorAll(".filter-btn");
  const currencyButtons = document.querySelectorAll(".currency-btn");
  const cartToggle = document.getElementById("cart-toggle");
  const cartOverlay = document.getElementById("cart-overlay");
  const closeCartButton = document.getElementById("close-cart");

  if (searchInput) {
    searchInput.addEventListener("input", () => {
      renderProducts(getVisibleProducts());
    });
  }

  filterButtons.forEach((button) => {
    button.addEventListener("click", () => {
      state.activeCategory = button.dataset.categoryId;
      document.querySelectorAll(".filter-btn").forEach((btn) => {
        btn.classList.toggle("active", btn === button);
      });
      renderProducts(getVisibleProducts());
    });
  });

  currencyButtons.forEach((button) => {
    button.addEventListener("click", () => {
      state.currency = button.dataset.currency;
      updateCurrencyUI();
    });
  });

  document.addEventListener("click", (event) => {
    const target = event.target;
    const addButton = target.closest("[data-add-to-cart]");
    const cartAction = target.closest("[data-cart-action]");

    if (addButton) {
      addToCart(addButton.dataset.addToCart);
    }

    if (cartAction) {
      adjustCartItem(cartAction.dataset.productId, cartAction.dataset.cartAction);
    }
  });

  if (cartToggle) {
    cartToggle.addEventListener("click", () => {
      document.body.classList.add("cart-open");
    });
  }

  if (cartOverlay) {
    cartOverlay.addEventListener("click", () => {
      document.body.classList.remove("cart-open");
    });
  }

  if (closeCartButton) {
    closeCartButton.addEventListener("click", () => {
      document.body.classList.remove("cart-open");
    });
  }
}

/**
 * Initialize the catalog and the cart on page load.
 */
function initCatalog() {
  renderProducts(getVisibleProducts());
  updateCurrencyUI();
  updateCartDisplay();
  bindEvents();
}

document.addEventListener("DOMContentLoaded", initCatalog);
