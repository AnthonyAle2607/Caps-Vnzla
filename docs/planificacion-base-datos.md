# Planificación de base de datos local y administración

## Objetivo

Consolidar SQLite como base de datos local de desarrollo para CAPS VNZLA, manteniendo una estructura preparada para crecer hacia PostgreSQL en producción.

## Modelo propuesto

### Tablas actuales

- `categorias`: clasificación de productos.
- `productos`: código, nombre, descripción, precio, stock, estado y categoría.
- `imagenes_producto`: galería e imagen principal de cada producto.
- `etiquetas`: etiquetas comerciales.
- `producto_etiqueta`: relación muchos a muchos entre productos y etiquetas.

### Tabla añadida

- `colecciones`: nombre, slug, descripción, imagen, estado y orden de presentación.

## Fases de implementación

### Fase 1: persistencia local

1. Mantener SQLite como motor local.
2. Centralizar la ruta mediante `DATABASE_URL`.
3. Crear tablas con SQLAlchemy.
4. Mantener datos iniciales únicamente cuando la tabla correspondiente esté vacía.
5. Evitar borrar o sobrescribir registros existentes.

### Fase 2: migraciones

Usar Flask-Migrate para versionar cambios del esquema:

```powershell
flask --app run.py db init
flask --app run.py db migrate -m "Crear tabla de colecciones"
flask --app run.py db upgrade
```

En una base ya existente, se debe revisar la migración generada antes de aplicarla.

### Fase 3: administración

La ruta `/admin/` incorpora una vista inicial de solo lectura con:

- total de productos,
- productos activos,
- categorías,
- colecciones activas,
- inventario reciente.

Antes de permitir edición, creación o eliminación se debe incorporar autenticación, autorización por roles, validación de formularios, protección CSRF y registro de auditoría.

### Fase 4: operación comercial

1. Añadir pedidos y líneas de pedido.
2. Descontar stock mediante operaciones transaccionales.
3. Registrar clientes y direcciones.
4. Integrar pagos y estados de envío.
5. Crear copias de seguridad periódicas.

## Reglas de integridad

- `codigo`, `slug` y valores identificadores deben ser únicos.
- Los precios no deben aceptar valores negativos.
- El stock debe ser un entero mayor o igual que cero.
- Una imagen principal debe pertenecer a un producto existente.
- Las colecciones inactivas no deben mostrarse en la tienda.

## Entornos

- Desarrollo: SQLite local en `caps_vnzla.db`.
- Pruebas: SQLite temporal por configuración.
- Producción: PostgreSQL mediante `DATABASE_URL`.

## Respaldo local

Antes de aplicar migraciones o cambios estructurales:

1. Copiar `caps_vnzla.db`.
2. Ejecutar la migración.
3. Probar `/`, `/producto/1` y `/admin/`.
4. Verificar que el catálogo y las colecciones carguen correctamente.
