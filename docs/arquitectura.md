# Arquitectura del proyecto CAPS VNZLA

## 1. Propósito del sistema

CAPS VNZLA es una tienda web de gorras con catálogo interactivo, colecciones, checkout por WhatsApp e inventario administrable. El panel privado ofrece herramientas de gestión y un análisis orientativo de ventas.

## 2. Enfoque de arquitectura

El proyecto usa una estructura basada en Flask con patrón de fábrica de aplicación (`create_app`) y separación por capas:

- Presentación: templates Jinja2 + CSS + JS.
- Lógica de negocio: blueprints del catálogo y administración.
- Persistencia: SQLAlchemy con SQLite para desarrollo local o PostgreSQL mediante `DATABASE_URL`.
- Evolución del esquema: Flask-Migrate y migraciones versionadas.
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
- `ColorProducto`: registra colores disponibles.
- `Coleccion`: agrupa productos en páginas comerciales independientes.
- `Administrador`: autentica al personal y evalúa permisos de rol.
- `Pedido` y `PedidoItem`: guardan los datos del cliente y los importes históricos, incluidos precio y costo unitarios.
- `MovimientoStock`: conserva el historial de entradas, salidas y ajustes.

Cada clase incluye `to_dict()` para serializar datos al frontend o a la API JSON.

### 3.3. `app/views/catalog.py`

Expone las rutas públicas del catálogo, las colecciones, el checkout y la API:

- `/`: vista principal del storefront.
- `/coleccion/<slug>`: página propia de una colección con sus productos activos.
- `/producto/<id>`: vista de detalle del producto.
- `/checkout`: valida el inventario, registra el pedido y crea el enlace de WhatsApp.
- `/api/productos`: catálogo dinámico filtrable por categoría y texto.
- `/api/moneda`: tasa de conversión USD/BS.

### 3.4. `app/views/admin.py`

Protege las operaciones administrativas y comprueba los permisos en el servidor:

- `/admin/`: resumen, catálogo e inventario.
- `/admin/ventas`: ingresos registrados, rentabilidad estimada y reposición sugerida.
- Rutas para productos, colecciones, pedidos y movimientos de stock.

### 3.5. `app/templates/`

Contiene los componentes HTML del storefront y del panel. La plantilla base aporta:

- header con navegación,
- selector de moneda,
- botón de carrito,
- panel lateral del carrito,
- carga de scripts compartidos.

### 3.6. `app/static/`

Agrupa los recursos frontend:

- `css/style.css`: paleta visual y layout del catálogo.
- `js/catalog.js`: renderizado, filtros, conversión y lógica del carrito.

## 4. Flujo funcional

1. El usuario entra a la página principal.
2. El backend entrega JSON con productos activos y categorías.
3. El JavaScript renderiza tarjetas con imágenes, nombre, descripción y precio.
4. El usuario puede buscar, filtrar y cambiar moneda.
5. El carrito se guarda en `localStorage` para conservar la orden en la sesión.
6. El detalle público muestra información, precio, disponibilidad y productos recomendados.
7. En el checkout, el servidor valida el inventario y registra las líneas y movimientos de stock en una transacción.
8. El comprador confirma el pedido mediante el enlace generado a WhatsApp.
9. El dashboard analiza solicitudes de pedido; no representa pagos confirmados.

## 5. Modelo de datos

El modelo principal se describe de la siguiente forma:

- `Categoria` tiene muchos `Producto`.
- `Producto` pertenece a una `Categoria`.
- `Producto` tiene muchas `ImagenProducto`.
- `Producto` puede tener varias `Etiqueta`.
- `Producto` puede pertenecer a varias `Coleccion` y tener varios `ColorProducto`.
- `Pedido` tiene muchas `PedidoItem`; cada línea conserva el nombre, precio y costo vigentes al registrarse.
- Cada salida de inventario puede quedar vinculada a un `Pedido`.

Esto facilita una estructura de catálogo con alta extensibilidad y facilidad para futuras integraciones.

## 6. Decisiones clave

- El motor se configura mediante el entorno: SQLite facilita pruebas locales y PostgreSQL es compatible para despliegues.
- Separación entre frontend y backend para facilitar la escalabilidad del catálogo.
- Datos iniciales precargados para facilitar demostración sin configuración extra.
- Conversión de moneda centralizada en el backend y visible en el frontend.
- El margen y la reposición son estimaciones; el dashboard explica su cobertura y sus limitaciones.

## 7. Extensiones recomendadas

- Integración con pagos y notificaciones.
- Gestión administrativa de usuarios y restablecimiento de acceso.
- Estados de pedido y conciliación de pagos.
- Protección CSRF, rate limiting y uso de tipos decimales para importes.
