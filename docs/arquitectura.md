# Arquitectura del proyecto CAPS VNZLA

## 1. Propósito del sistema

CAPS VNZLA es un storefront para la venta de gorras con enfoque premium y estilo urbano. El sistema busca entregar una experiencia de compra rápida, limpia y visualmente sólida, con catálogo interactivo, filtros, moneda de conversión y carrito de orden.

## 2. Enfoque de arquitectura

El proyecto usa una estructura basada en Flask con patrón de fábrica de aplicación (`create_app`) y separación por capas:

- Presentación: templates Jinja2 + CSS + JS.
- Lógica de negocio: blueprints y endpoints del catálogo.
- Persistencia: SQLAlchemy con SQLite.
- Configuración: variables de entorno y clase `Config`.

## 3. Componentes principales

### 3.1. `app/__init__.py`

Responsable de:

- inicializar Flask,
- cargar variables de entorno,
- crear la instancia de SQLAlchemy,
- registrar blueprints,
- ejecutar la semilla de datos iniciales cuando no existe catálogo.

### 3.2. `app/models.py`

Define los modelos del dominio:

- `Categoria`: agrupa productos por tipo.
- `Producto`: almacena nombre, código, descripción, precio, stock y asociaciones.
- `ImagenProducto`: organiza imágenes y define la imagen principal.
- `Etiqueta`: clasifica o marca los productos.

Cada clase incluye `to_dict()` para serializar datos al frontend o a la API JSON.

### 3.3. `app/views/catalog.py`

Expone las rutas de público del catálogo y las API:

- `/`: vista principal del storefront.
- `/producto/<id>`: vista de detalle del producto.
- `/api/productos`: catálogo dinámico filtrable por categoría y texto.
- `/api/moneda`: tasa de conversión USD/BS.

### 3.4. `app/templates/`

Contiene todos los componentes HTML reutilizables y específicos del storefront. La plantilla base aporta:

- header con navegación,
- selector de moneda,
- botón de carrito,
- panel lateral del carrito,
- carga de scripts compartidos.

### 3.5. `app/static/`

Agrupa los recursos frontend:

- `css/style.css`: paleta visual y layout del catálogo.
- `js/catalog.js`: renderizado, filtros, conversión y lógica del carrito.

## 4. Flujo funcional

1. El usuario entra a la página principal.
2. El backend entrega JSON con productos activos y categorías.
3. El JavaScript renderiza tarjetas con imágenes, nombre, descripción y precio.
4. El usuario puede buscar, filtrar y cambiar moneda.
5. El carrito se guarda en `localStorage` para conservar la orden en la sesión.
6. El backend convierte y sirve los datos necesarios para el detalle del producto.

## 5. Modelo de datos

El modelo principal se describe de la siguiente forma:

- `Categoria` tiene muchos `Producto`.
- `Producto` pertenece a una `Categoria`.
- `Producto` tiene muchas `ImagenProducto`.
- `Producto` puede tener varias `Etiqueta`.

Esto facilita una estructura de catálogo con alta extensibilidad y facilidad para futuras integraciones.

## 6. Decisiones clave

- Uso de SQLite para reducir complejidad inicial y permitir desarrollo rápido.
- Separación entre frontend y backend para facilitar la escalabilidad del catálogo.
- Datos iniciales precargados para facilitar demostración sin configuración extra.
- Conversión de moneda centralizada en el backend y visible en el frontend.

## 7. Extensiones recomendadas

- Admin para crear y editar productos.
- Manejo de inventario por SKU.
- Checkout con formulario de entrega.
- Integración con pagos y notificaciones.
- Autenticación de usuarios y historial de compras.
