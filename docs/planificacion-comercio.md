# Planificación del módulo comercial

## Alcance implementado

- Administradores con usuario, contraseña cifrada, rol y estado activo.
- Permisos mínimos: `ver_panel` y `editar_productos`.
- Edición protegida de productos desde `/admin/productos/<id>/editar`.
- Alta de productos con código, precio, stock, categoría, colores y galería.
- Asignación de productos a varias colecciones desde ambos formularios.
- Creación, edición, publicación y retirada de colecciones en la portada.
- Retirada de productos del catálogo sin borrar datos vinculados a pedidos.
- Carga de imágenes JPEG, PNG y WebP validadas con límite de 5 MB y 40 MP por archivo.
- Página propia para cada colección con su galería de productos activos.
- Registro opcional del costo de compra por producto y copia del costo en cada
  pedido para consultar márgenes históricos.
- Dashboard con filtros de 7, 30 y 90 días, ingresos de productos, utilidad bruta
  estimada, productos más rentables y reposición sugerida a 30 días.
- Registro de pedidos sin cuenta de cliente.
- Datos personales y dirección guardados junto al pedido.
- Validación de stock antes de confirmar.
- Descuento transaccional del stock al registrar el pedido.
- Historial de ajustes manuales y salidas por pedido.
- Redirección a WhatsApp mediante el número configurado.

## Flujo del cliente

1. Agrega productos al carrito local.
2. Selecciona «Procesar pedido».
3. Completa nombre, teléfono, correo, dirección y referencia opcional.
4. El servidor valida productos y stock vigente.
5. Se registra el pedido y sus líneas.
6. Se descuenta el stock.
7. Se registra un movimiento por cada producto.
8. Se muestra un enlace a WhatsApp con el resumen del pedido.

## Flujo administrativo

1. Visita `/admin/login`.
2. Inicia sesión con el usuario configurado.
3. Consulta el panel, pedidos y movimientos.
4. Crea y edita productos, carga hasta ocho imágenes y administra colores e inventario.
5. Asigna productos a una o varias colecciones para organizarlos en la portada.
6. Crea, ordena, edita, publica o retira colecciones desde la administración.
7. Retira productos de la tienda sin eliminar su historial comercial.
8. Los cambios manuales de stock y las altas con inventario inicial generan un movimiento.

## Dashboard de ventas y reposición

- Ventas: `/admin/ventas`.
- El período analizable se puede cambiar a 7, 30 o 90 días.
- Los ingresos se calculan sobre el precio de las líneas de pedido y excluyen
  el costo de envío.
- La utilidad bruta estima `precio unitario − costo de compra capturado` por
  unidad pedida y solo aparece para costos conocidos. El costo se congela en
  cada nueva línea de pedido.
- El margen porcentual usa únicamente los ingresos de líneas con costo
  conocido; la cobertura indica qué proporción de unidades cuenta con ese dato.
- Los pedidos se registran al enviar el formulario y todavía deben confirmarse
  por WhatsApp; por esto la vista informa solicitudes e ingresos registrados,
  no pagos liquidados ni ventas confirmadas.
- Los registros previos a la captura del costo conservan el costo como
  desconocido y no se incluyen en la estimación de utilidad.
- La sugerencia de reposición proyecta las unidades solicitadas al ritmo
  observado durante el período hacia 30 días y resta el inventario actual. Es
  una referencia operativa, no una orden de compra ni un pronóstico garantizado.

## Administración del catálogo

- Productos: `/admin/productos/nuevo`; desde el panel se pueden editar, publicar o
  retirar del catálogo. La retirada conserva el registro y sus referencias en los
  pedidos anteriores.
- Colecciones: `/admin/colecciones`; permite gestionar portada, descripción,
  orden, visibilidad y los productos asignados.
- La portada muestra los productos activos asignados a cada colección.
- Las imágenes se guardan localmente bajo `app/static/img/productos/` con nombres
  generados por el servidor. Cada archivo se valida por formato y tamaño.
- Se aceptan imágenes JPEG, PNG y WebP verificadas con Pillow, hasta 5 MB y 40
  megapíxeles por archivo, con un máximo de ocho fotos por producto.
- Al reemplazar o retirar una imagen, el archivo local solo se elimina si ninguna
  ficha o colección lo sigue usando.

## Configuración obligatoria

En `.env` se recomienda definir valores propios:

```env
WHATSAPP_PHONE=584122967035
ADMIN_DEFAULT_USERNAME=admin
ADMIN_DEFAULT_PASSWORD=una-clave-larga-y-segura
```

El usuario administrador inicial solo se crea cuando no existen administradores. Después de crear la cuenta, el cambio de contraseña debe implementarse antes de poner el sistema en producción.

## Siguiente endurecimiento

- CSRF con Flask-WTF.
- Rate limiting en el inicio de sesión.
- Gestión de administradores desde el panel.
- Cambio y recuperación de contraseña.
- Estados de pedido editables.
- Validación estricta de correo y teléfono.
- Uso de `Decimal` para importes monetarios.
