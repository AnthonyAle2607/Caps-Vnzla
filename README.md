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

- `app/__init__.py`: creación de la app, configuración centralizada y carga inicial de datos.
- `app/config.py`: variables globales y configuración del entorno.
- `app/models.py`: modelos SQLAlchemy para categorías, productos, imágenes y etiquetas.
- `app/views/catalog.py`: rutas públicas del catálogo y endpoints JSON.
- `app/templates/`: plantillas HTML Jinja2 para la vista base y detalle del producto.
- `app/static/`: estilos CSS, scripts JavaScript y recursos visuales del storefront.

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

La aplicación quedará disponible en http://localhost:5000.

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
- Catálogo interactivo con búsqueda y filtros.
- Tarjetas de productos con descripción bajo la imagen.
- Carrito lateral con opciones de cantidad.
- Conversión automática entre USD y BS.
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
│   └── planificacion.md
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── run.py
└── caps_vnzla.db
```

## Personalización

Para ajustar la tasa de cambio, editar el archivo `.env` o la variable `CURRENCY_RATE_BS`.

## Posibles extensiones

- panel administrativo,
- gestión de stock,
- proceso de pago,
- autenticación,
- manejo de promociones y descuentos,
- escalado con base de datos real y migraciones.
