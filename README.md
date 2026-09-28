# CAPS VNZLA

Plataforma web para la venta de gorras con una estética urbana premium inspirada en la paleta de la marca: amarillo #FFCC00, negro #111827, gris claro #A0A0A0 y fondo principal blanco para mejorar legibilidad, contraste y presentación de productos.

## Objetivo del proyecto

Construir un catálogo interactivo y comercial que permita:

- mostrar productos premium con una presentación visual clara,
- navegar por categorías y filtros,
- buscar por nombre o descripción,
- cambiar entre USD y BS con tasa configurable,
- agregar artículos al carrito con cantidades,
- mantener una estructura modular, escalable y bien documentada.

## Visión de producto

La tienda está diseñada como una experiencia de compra moderna para una marca streetwear con identidad premium. El eje visual prioriza:

- fondo principal blanco para reforzar la limpieza y el lujo discreto,
- detalles en amarillo para captar atención y reforzar la identidad de marca,
- tarjetas de producto con imagen superior, título, descripción y precio claramente diferenciados,
- navegación simple y directiva con acceso rápido al catálogo y al carrito.

## Arquitectura

El proyecto sigue el patrón MVC / application factory de Flask:

- `app/__init__.py`: creación de la app, configuración centralizada y semilla de datos para SQLite.
- `app/config.py`: variables globales y configuración del entorno.
- `app/models.py`: modelos SQLAlchemy para catálogo, colecciones, administradores, pedidos e inventario.
- `app/views/catalog.py`: páginas públicas, checkout, colecciones y endpoints JSON.
- `app/views/admin.py`: autenticación, catálogo, pedidos, colecciones e informes comerciales.
- `app/templates/`: plantillas Jinja2 del storefront y del panel administrativo.
- `app/static/`: estilos CSS, scripts JavaScript e imágenes.
- `migrations/`: historial versionado del esquema de la base de datos.

## Requisitos

- Python 3.11+
- pip
- Entorno virtual recomendado

## Instalación

1. Crear entorno virtual:
   ```bash
   python -m venv .venv
   ```

2. Activar entorno:
   - Windows:
     ```powershell
     .\.venv\Scripts\activate
     ```
   - Linux/macOS:
     ```bash
     source .venv/bin/activate
     ```

3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Crear archivo de entorno:
   ```bash
   copy .env.example .env
   ```

5. Ejecutar app:
   ```bash
   python run.py
   ```

Para aplicar cambios pendientes del esquema:

```bash
flask --app run.py db upgrade
```

La aplicación quedará disponible en http://localhost:5000.

## Despliegue en Vercel con Supabase

El punto de entrada de Flask para Vercel es `index.py`. Para desplegar:

1. Sube el proyecto a GitHub e impórtalo en Vercel; deja como raíz del proyecto
   la carpeta que contiene `index.py` y `requirements.txt`.
2. En la configuración del proyecto en Vercel, agrega estas variables para los
   entornos que vayas a utilizar:
   - `DATABASE_URL`: cadena PostgreSQL de Supabase. La configuración selecciona
     automáticamente el driver `psycopg` incluido en las dependencias.
   - `SECRET_KEY`: secreto aleatorio y exclusivo de producción.
   - `ADMIN_DEFAULT_USERNAME` y `ADMIN_DEFAULT_PASSWORD`: credenciales iniciales
     seguras para crear el administrador.
   - `CURRENCY_RATE_BS`, `SHIPPING_COST_USD` y `WHATSAPP_PHONE`.
3. Antes de abrir la tienda, ejecuta las migraciones contra la base de Supabase
   desde un entorno local que tenga esas mismas variables configuradas:

   ```bash
   flask --app index:app db upgrade
   ```

4. Para crear los datos iniciales en una base recién migrada, ejecuta una sola
   vez:

   ```bash
   python -c "from index import app; from app import seed_data; ctx=app.app_context(); ctx.push(); seed_data(); ctx.pop()"
   ```

   Define las credenciales administrativas antes de hacerlo. `seed_data()`
   añade el catálogo de demostración si la base está vacía; no reemplaza datos
   existentes.
5. Despliega primero como Preview y prueba el catálogo, login, compras y conexión
   a la base. No publiques el archivo `.env` ni copies sus valores a Git.

Las imágenes que ya forman parte del repositorio se despliegan junto con el
código. Las imágenes nuevas que se carguen desde el administrador se guardan hoy
en el disco local; ese almacenamiento no es persistente en Vercel. Para usar
cargas de imágenes en producción, configura Supabase Storage u otro servicio de
archivos y adapta el flujo de subida del administrador antes de depender de él.

## Documentación técnica

Todo el código base tiene comentarios y/o docstrings explicando:

- propósito del módulo o función,
- entradas y salidas esperadas,
- dependencias internas,
- decisiones relevantes para mantenimiento y escalabilidad.

La documentación adicional del proyecto se encuentra en la carpeta `docs/`.

## Planificación del proyecto

### Fase 1: base visual y estructura
- Definir paleta y sistema visual premium.
- Crear la base HTML con header, hero y estructura del catálogo.
- Diseñar tarjetas de producto con descripción y CTA claros.

### Fase 2: interactividad comercial
- Implementar búsqueda y filtros por categoría.
- Integrar selector de monedas USD/BS.
- Construir carrito lateral con actualización dinámica y cantidades.

### Fase 3: catálogo y detalle del producto
- Renderizar productos desde datos estructurados.
- Exponer endpoints API para catálogo y moneda.
- Mostrar detalle del producto con stock y precio convertido.

### Fase 4: documentación y mantenimiento
- Documentar arquitectura, decisiones y flujo del usuario.
- Preparar extensiones futuras: admin, checkout, promociones e inventario.

## Funcionalidades actuales

- Header con navegación y selector de moneda.
- Hero principal con branding visual.
- Marca de agua PNG transparente del monograma «RR» en antracita, integrada con desvanecimiento en el fondo negro del hero y sin recuadro.
- Catálogo interactivo con búsqueda y filtros.
- Tarjetas de productos con descripción bajo la imagen.
- Carrito lateral con opciones de cantidad.
- Conversión automática entre USD y BS.
- Colecciones con página propia y productos asignados.
- Checkout con dirección de entrega y enlace de confirmación por WhatsApp.
- Panel administrativo y dashboard comercial disponible en `/admin/ventas`.
- Plantilla reutilizable con base HTML y estilos globales.

## Estructura del proyecto

```text
Caps-Vnzla/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   ├── static/
│   │   ├── css/
│   │   ├── img/
│   │   └── js/
│   ├── templates/
│   │   ├── base.html
│   │   └── catalog/
│   └── views/
│       ├── __init__.py
│       └── catalog.py
├── docs/
│   ├── arquitectura.md
│   ├── planificacion-comercio.md
│   └── planificacion-base-datos.md
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── run.py
└── caps_vnzla.db
```

## Personalización

Para ajustar la tasa de cambio, editar el archivo `.env` o la variable `CURRENCY_RATE_BS`.

## Base de datos local y administración

La aplicación usa SQLAlchemy y Flask-Migrate. SQLite permite trabajar en local;
el motor se configura con `DATABASE_URL` (también compatible con PostgreSQL).
En SQLite, la app crea tablas ausentes y carga datos de demostración si hace
falta catálogo. Para otros motores, aplica las migraciones con Flask-Migrate.

- Catálogo público: `http://localhost:5000/`
- Panel administrativo: `http://localhost:5000/admin/`
- Análisis de ventas: `http://localhost:5000/admin/ventas`
- Checkout: `http://localhost:5000/checkout`
- Plan técnico: [`docs/planificacion-base-datos.md`](docs/planificacion-base-datos.md)

El panel administrativo requiere inicio de sesión y permite administrar el
catálogo desde `http://localhost:5000/admin/`:

- Crear, editar, publicar y retirar productos sin perder el historial de pedidos.
- Ajustar precio, descripción, categoría, inventario y colores disponibles.
- Cargar una galería de hasta ocho imágenes JPEG, PNG o WebP por producto.
- Crear, ordenar, editar, publicar y retirar colecciones.
- Asignar productos a una o varias colecciones; cada colección tiene su propia
  página con productos, precios y existencias.
- Consultar pedidos y movimientos de inventario.
- Registrar opcionalmente el costo de compra unitario, además del precio de venta.
- Revisar un dashboard con ingresos, utilidad bruta estimada, productos más
  rentables y una sugerencia orientativa de reposición a 30 días.

Las imágenes cargadas desde administración se guardan en
`app/static/img/productos/`. Se validan con Pillow y admiten un máximo de 5 MB y
40 megapíxeles por archivo.

La rentabilidad solo incluye costos capturados al registrar cada pedido. Los
pedidos son solicitudes enviadas a WhatsApp pendientes de confirmación, por lo
que el dashboard no representa pagos liquidados. La sugerencia de reposición
proyecta el ritmo de pedidos reciente y no sustituye una decisión de compra.

## Posibles extensiones

- manejo de promociones y descuentos,
- integración de pagos y confirmación automática de pedidos,
- controles adicionales de acceso y recuperación de contraseña.
