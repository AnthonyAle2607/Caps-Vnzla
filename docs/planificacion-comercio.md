# Planificación del módulo comercial

## Alcance implementado

- Administradores con usuario, contraseña cifrada, rol y estado activo.
- Permisos mínimos: `ver_panel` y `editar_productos`.
- Edición protegida de productos desde `/admin/productos/<id>/editar`.
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
4. Edita productos si su rol tiene `editar_productos`.
5. Los cambios manuales de stock generan un movimiento.

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
- Migraciones versionadas con Flask-Migrate.
