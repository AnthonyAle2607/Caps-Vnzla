/**
 * Lógica del catálogo frontend de CAPS VNZLA.
 *
 * Este módulo controla el renderizado de productos, los filtros, la búsqueda,
 * la conversión USD/BS, el carrusel y el comportamiento del carrito.
 */

const productData = Array.isArray(window.catalogData) ? window.catalogData : [];
const cartStorageKey = "caps_vnzla_cart";
const state = {
  currency: localStorage.getItem("caps_vnzla_currency") || "USD",
  rate: Number(window.currencyRate || 35),
  cart: loadCart(),
  activeCategory: "all",
  carouselTimer: null,
  carouselIndex: 0,
  isDragging: false,
  dragStartX: 0,
  dragStartScrollLeft: 0,
};

/**
 * Carga el carrito guardado en localStorage.
 *
 * @returns {Array<{id: number, name: string, price_usd: number, quantity: number}>}
 */
function loadCart() {
  try {
    const raw = localStorage.getItem(cartStorageKey);
    return raw ? JSON.parse(raw) : [];
  } catch (error) {
    console.warn("No se pudo cargar el carrito desde localStorage:", error);
    return [];
  }
}

/**
 * Guarda el estado del carrito para conservar la orden entre sesiones.
 */
function saveCart() {
  localStorage.setItem(cartStorageKey, JSON.stringify(state.cart));
}

/**
 * Formatea un valor numérico en la moneda activa.
 *
 * @param {number} value - Valor base en dólares.
 * @param {string} currency - Moneda destino: USD o BS.
 * @returns {string} Precio listo para mostrar.
 */
function formatMoney(value, currency = state.currency) {
  const numericValue = Number(value || 0);

  if (currency === "BS") {
    return `Bs ${numericValue * state.rate}`.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }

  return `$ ${numericValue.toFixed(2)}`;
}

/**
 * Convierte un precio en dólares a la moneda seleccionada.
 *
 * @param {number} priceUsd - Precio del producto en dólares.
 * @returns {number} Precio convertido.
 */
function convertPrice(priceUsd) {
  return state.currency === "BS" ? Number(priceUsd) * state.rate : Number(priceUsd);
}

/**
 * Actualiza la moneda visible y vuelve a renderizar los componentes dependientes.
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
 * Devuelve los productos filtrados por categoría y texto de búsqueda.
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
 * Renderiza los productos dentro del carrusel principal.
 *
 * @param {Array<Object>} products - Lista de productos que se mostrará.
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
  bindAddToCartButtons(container);
  state.carouselIndex = 0;
  configureCarousel();
}

/**
 * Avanza el carrusel una tarjeta y vuelve al inicio al llegar al final.
 *
 * @param {number} direction - Dirección: 1 para avanzar y -1 para retroceder.
 */
function moveCarousel(direction) {
  const viewport = document.querySelector(".product-carousel__viewport");
  const cards = document.querySelectorAll(".product-card");
  if (!viewport || cards.length === 0) {
    return;
  }

  state.carouselIndex = (state.carouselIndex + direction + cards.length) % cards.length;
  const activeCard = cards[state.carouselIndex];
  const viewportBounds = viewport.getBoundingClientRect();
  const cardBounds = activeCard.getBoundingClientRect();
  const horizontalOffset = cardBounds.left - viewportBounds.left + viewport.scrollLeft;

  viewport.scrollTo({
    left: horizontalOffset,
    behavior: "smooth",
  });
}

/**
 * Reinicia el avance automático del carrusel.
 */
function restartCarouselTimer() {
  window.clearInterval(state.carouselTimer);
  state.carouselTimer = window.setInterval(() => moveCarousel(1), 4500);
}

/**
 * Configura controles, autoplay y arrastre táctil o con ratón.
 */
function configureCarousel() {
  const carousel = document.querySelector("[data-carousel]");
  const viewport = document.querySelector(".product-carousel__viewport");
  if (!carousel || !viewport || carousel.dataset.ready === "true") {
    restartCarouselTimer();
    return;
  }

  carousel.dataset.ready = "true";
  const previousButton = carousel.querySelector("[data-carousel-prev]");
  const nextButton = carousel.querySelector("[data-carousel-next]");
  if (previousButton) {
    previousButton.addEventListener("click", () => {
      moveCarousel(-1);
      restartCarouselTimer();
    });
  }
  if (nextButton) {
    nextButton.addEventListener("click", () => {
      moveCarousel(1);
      restartCarouselTimer();
    });
  }

  viewport.addEventListener("pointerdown", (event) => {
    if (
      event.target instanceof Element
      && event.target.closest("a, button, input, label")
    ) {
      return;
    }
    state.isDragging = true;
    state.dragStartX = event.clientX;
    state.dragStartScrollLeft = viewport.scrollLeft;
    viewport.setPointerCapture(event.pointerId);
  });
  viewport.addEventListener("pointermove", (event) => {
    if (!state.isDragging) {
      return;
    }
    viewport.scrollLeft = state.dragStartScrollLeft - (event.clientX - state.dragStartX);
  });
  viewport.addEventListener("pointerup", () => {
    state.isDragging = false;
    restartCarouselTimer();
  });
  viewport.addEventListener("pointercancel", () => {
    state.isDragging = false;
    restartCarouselTimer();
  });

  restartCarouselTimer();
}

/**
 * Conecta una sola vez los botones de añadir al carrito.
 *
 * @param {Element|Document} root - Contenedor donde se buscarán los botones.
 */
function bindAddToCartButtons(root) {
  root.querySelectorAll("[data-add-to-cart]").forEach((button) => {
    if (button.dataset.cartBound === "true") {
      return;
    }
    button.dataset.cartBound = "true";
    button.addEventListener("click", () => {
      addToCart(button.dataset.addToCart);
    });
  });
}

/**
 * Agrega un producto al carrito o incrementa su cantidad si ya existe.
 *
 * @param {number} productId - Identificador del producto.
 */
function addToCart(productId) {
  const product = productData.find((item) => Number(item.id) === Number(productId));
  if (!product) {
    return;
  }

  const existingItem = state.cart.find((item) => Number(item.id) === Number(product.id));
  const selectedColor = document.querySelector('input[name="product-color"]:checked');
  const color = selectedColor ? selectedColor.value : (product.colores?.[0]?.nombre || "");

  if (existingItem) {
    existingItem.quantity += 1;
    existingItem.color = color || existingItem.color;
  } else {
    state.cart.push({
      id: Number(product.id),
      name: product.nombre,
      price_usd: Number(product.precio_usd),
      quantity: 1,
      color,
    });
  }

  saveCart();
  updateCartDisplay();
  const feedback = document.getElementById("detail-cart-feedback");
  if (feedback) {
    feedback.textContent = `${product.nombre} fue añadido al carrito.`;
  }
}

/**
 * Elimina o reduce la cantidad de un artículo del carrito.
 *
 * @param {number} productId - Identificador del producto.
 * @param {string} action - Acción: increase o decrease.
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
 * Actualiza los artículos y totales visibles del carrito.
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
            ${item.color ? `<small>Color: ${item.color}</small>` : ""}
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
 * Conecta los eventos de interacción después de cargar el DOM.
 */
function bindEvents() {
  const searchInput = document.getElementById("catalog-search");
  const filterButtons = document.querySelectorAll(".filter-btn");
  const currencyButtons = document.querySelectorAll(".currency-btn");
  const cartToggle = document.getElementById("cart-toggle");
  const cartOverlay = document.getElementById("cart-overlay");
  const closeCartButton = document.getElementById("close-cart");
  const checkoutButton = document.getElementById("checkout-button");
  bindAddToCartButtons(document);

  if (searchInput) {
    searchInput.addEventListener("input", () => {
      renderProducts(getVisibleProducts());
      restartCarouselTimer();
    });
  }

  filterButtons.forEach((button) => {
    button.addEventListener("click", () => {
      state.activeCategory = button.dataset.categoryId;
      document.querySelectorAll(".filter-btn").forEach((btn) => {
        btn.classList.toggle("active", btn === button);
      });
      renderProducts(getVisibleProducts());
      restartCarouselTimer();
    });
  });

  currencyButtons.forEach((button) => {
    button.addEventListener("click", () => {
      state.currency = button.dataset.currency;
      updateCurrencyUI();
    });
  });

  document.addEventListener("click", (event) => {
    if (!(event.target instanceof Element)) {
      return;
    }

    const target = event.target;
    const cartAction = target.closest("[data-cart-action]");

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

  if (checkoutButton) {
    checkoutButton.addEventListener("click", () => {
      if (!state.cart.length) {
        window.alert("Agrega al menos un producto antes de procesar el pedido.");
        return;
      }
      window.location.href = "/checkout";
    });
  }
}

/**
 * Inicializa el catálogo y el carrito cuando carga la página.
 */
function initCatalog() {
  renderProducts(getVisibleProducts());
  updateCurrencyUI();
  updateCartDisplay();
  bindEvents();
}

document.addEventListener("DOMContentLoaded", initCatalog);
