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
    const amountInBolivares = new Intl.NumberFormat("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(numericValue * state.rate);
    return `Bs ${amountInBolivares}`;
  }

  return `$ ${numericValue.toFixed(2)}`;
}

/**
 * Codifica texto de la base de datos antes de insertarlo en plantillas HTML.
 *
 * @param {string|number} value - Contenido que se mostrará en el catálogo.
 * @returns {string} Texto seguro para insertar como contenido HTML.
 */
function escapeHTML(value) {
  const entities = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
    "'": "&#39;",
  };

  return String(value ?? "").replace(/[&<>"']/g, (character) => entities[character]);
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
      (product) => {
        const productId = Number(product.id);
        const safeProductId = Number.isInteger(productId) && productId > 0 ? productId : 0;
        const collections = Array.isArray(product.colecciones)
          ? product.colecciones.map(escapeHTML).join(", ")
          : "";
        const labels = Array.isArray(product.etiquetas) ? product.etiquetas : [];
        const newLabel = labels.find((label) => String(label).toLowerCase() === "nuevo");
        const collectionLabel = Array.isArray(product.colecciones) ? product.colecciones[0] : "";
        const badge = newLabel
          ? `<span class="badge badge--primary">${escapeHTML(newLabel)}</span>`
          : collectionLabel
            ? `<span class="badge badge--collection">${escapeHTML(collectionLabel)}</span>`
            : Number(product.stock) > 0 && Number(product.stock) <= 5
              ? `<span class="badge badge--stock">Últimas ${escapeHTML(product.stock)}</span>`
              : "";
        const isAvailable = Number(product.stock) > 0;
        return `
        <article class="product-card">
          <a class="product-card__media" href="/producto/${safeProductId}" aria-label="Ver detalle de ${escapeHTML(product.nombre)}">
            <img src="${escapeHTML(product.imagen || "/static/img/placeholder.svg")}" alt="${escapeHTML(product.nombre)}" />
            ${badge}
            <span class="product-card__view-hint">Ver producto <span aria-hidden="true">↗</span></span>
          </a>
          <div class="product-card__body">
            <p class="product-card__category">${escapeHTML(product.categoria)}</p>
            ${collections ? `<p class="product-card__collections">${collections}</p>` : ""}
            <h3>${escapeHTML(product.nombre)}</h3>
            <p class="product-card__description">${escapeHTML(product.descripcion.slice(0, 100))}${product.descripcion.length > 100 ? "…" : ""}</p>
            <div class="product-card__meta">
              <span class="product-card__price">${formatMoney(product.precio_usd)}</span>
              <span class="product-card__stock ${isAvailable ? "" : "product-card__stock--empty"}">${isAvailable ? `${escapeHTML(product.stock)} disponibles` : "Agotado"}</span>
            </div>
            <div class="product-card__actions">
              <a href="/producto/${safeProductId}" class="secondary-button">Ver detalle</a>
              <button type="button" class="cta-button" data-add-to-cart="${safeProductId}" ${isAvailable ? "" : "disabled"}>${isAvailable ? "Añadir al carrito" : "Agotado"}</button>
            </div>
          </div>
        </article>
      `;
      },
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
      if (!button.disabled) {
        const originalLabel = button.textContent;
        button.textContent = "Añadido ✓";
        button.classList.add("is-added");
        window.setTimeout(() => {
          button.textContent = originalLabel;
          button.classList.remove("is-added");
        }, 1300);
      }
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
  const itemCount = state.cart.reduce((sum, item) => sum + item.quantity, 0);
  document.querySelectorAll("[data-mobile-cart-count]").forEach((element) => {
    element.textContent = element.classList.contains("mobile-cart-bar__count")
      ? String(itemCount)
      : `${itemCount} ${itemCount === 1 ? "artículo" : "artículos"}`;
  });

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
            <strong>${escapeHTML(item.name)}</strong>
            ${item.color ? `<small>Color: ${escapeHTML(item.color)}</small>` : ""}
            <span>${formatMoney(item.price_usd)}</span>
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

  subtotalDisplay.textContent = formatMoney(subtotal);
  totalDisplay.textContent = formatMoney(subtotal);
}

/**
 * Conecta los eventos de interacción después de cargar el DOM.
 */
function bindEvents() {
  const searchInput = document.getElementById("catalog-search");
  const filterButtons = document.querySelectorAll(".filter-btn");
  const currencyButtons = document.querySelectorAll(".currency-btn");
  const mobileMenuToggle = document.getElementById("mobile-menu-toggle");
  const navigation = document.getElementById("store-navigation");
  const cartOverlay = document.getElementById("cart-overlay");
  const closeCartButton = document.getElementById("close-cart");
  const cartPanel = document.getElementById("cart-panel");
  const checkoutButton = document.getElementById("checkout-button");
  let cartTriggerElement = null;
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

  /**
   * Cierra el menú móvil y sincroniza los atributos accesibles del botón.
   */
  const closeMobileMenu = () => {
    document.body.classList.remove("menu-open");
    mobileMenuToggle?.setAttribute("aria-expanded", "false");
    mobileMenuToggle?.setAttribute("aria-label", "Abrir menú de navegación");
  };

  mobileMenuToggle?.addEventListener("click", () => {
    const isOpen = document.body.classList.toggle("menu-open");
    mobileMenuToggle.setAttribute("aria-expanded", String(isOpen));
    mobileMenuToggle.setAttribute(
      "aria-label",
      isOpen ? "Cerrar menú de navegación" : "Abrir menú de navegación",
    );
  });

  navigation?.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", closeMobileMenu);
  });

  /**
   * Abre el cajón del carrito, lleva el foco a su cierre y recuerda el origen.
   *
   * @param {Element} trigger - Botón que solicitó abrir el carrito.
   */
  const openCart = (trigger) => {
    closeMobileMenu();
    cartTriggerElement = trigger;
    document.body.classList.add("cart-open");
    cartPanel?.setAttribute("aria-hidden", "false");
    if (cartPanel) {
      cartPanel.inert = false;
    }
    closeCartButton?.focus();
  };

  document.querySelectorAll("[data-cart-open]").forEach((trigger) => {
    trigger.addEventListener("click", () => openCart(trigger));
  });

  /**
   * Cierra el carrito y devuelve el foco al botón que lo abrió.
   */
  const closeCart = () => {
    document.body.classList.remove("cart-open");
    cartPanel?.setAttribute("aria-hidden", "true");
    if (cartPanel) {
      cartPanel.inert = true;
    }
    cartTriggerElement?.focus();
    cartTriggerElement = null;
  };

  if (cartOverlay) {
    cartOverlay.addEventListener("click", closeCart);
  }

  if (closeCartButton) {
    closeCartButton.addEventListener("click", closeCart);
  }

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      if (document.body.classList.contains("cart-open")) {
        closeCart();
      } else {
        closeMobileMenu();
      }
    }

    if (event.key === "Tab" && document.body.classList.contains("cart-open") && cartPanel) {
      const focusable = Array.from(
        cartPanel.querySelectorAll('button:not(:disabled), a[href], input:not(:disabled), [tabindex="0"]'),
      );
      if (!focusable.length) {
        event.preventDefault();
        cartPanel.focus();
        return;
      }
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
  });

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
