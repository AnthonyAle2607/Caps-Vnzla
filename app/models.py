"""Modelos de base de datos del catálogo CAPS VNZLA."""

from __future__ import annotations

from app import db
from datetime import datetime

producto_etiqueta = db.Table(
    "producto_etiqueta",
    db.Column("producto_id", db.Integer, db.ForeignKey("productos.id"), primary_key=True),
    db.Column("etiqueta_id", db.Integer, db.ForeignKey("etiquetas.id"), primary_key=True),
)


class Administrador(db.Model):
    """Usuario autorizado para acceder al panel administrativo."""

    __tablename__ = "administradores"

    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(80), unique=True, nullable=False)
    nombre = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(30), nullable=False, default="editor")
    activo = db.Column(db.Boolean, nullable=False, default=True)
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def tiene_permiso(self, permiso: str) -> bool:
        """Indica si el rol actual puede ejecutar un permiso."""
        return self.activo and (self.rol == "superadmin" or permiso in {"ver_panel", "editar_productos"})


class Pedido(db.Model):
    """Pedido creado por un cliente sin necesidad de registrarse."""

    __tablename__ = "pedidos"

    id = db.Column(db.Integer, primary_key=True)
    nombre_cliente = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(30), nullable=False)
    correo = db.Column(db.String(160), nullable=False)
    direccion = db.Column(db.Text, nullable=False)
    referencia = db.Column(db.String(160), nullable=True)
    total_usd = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(30), nullable=False, default="pendiente")
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    items = db.relationship("PedidoItem", backref="pedido", cascade="all, delete-orphan", lazy=True)


class PedidoItem(db.Model):
    """Producto y cantidad congelados dentro de un pedido."""

    __tablename__ = "pedido_items"

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedidos.id"), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    nombre_producto = db.Column(db.String(150), nullable=False)
    precio_usd = db.Column(db.Float, nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    producto = db.relationship("Producto", lazy=True)


class MovimientoStock(db.Model):
    """Registra cada entrada o salida de inventario."""

    __tablename__ = "movimientos_stock"

    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    stock_anterior = db.Column(db.Integer, nullable=False)
    stock_nuevo = db.Column(db.Integer, nullable=False)
    motivo = db.Column(db.String(255), nullable=False)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedidos.id"), nullable=True)
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    producto = db.relationship("Producto", lazy=True)


class Coleccion(db.Model):
    """Representa una colección comercial visible en la tienda."""

    __tablename__ = "colecciones"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    imagen_url = db.Column(db.String(255), nullable=False)
    activa = db.Column(db.Boolean, nullable=False, default=True)
    orden = db.Column(db.Integer, nullable=False, default=0)

    def to_dict(self) -> dict:
        """Devuelve los datos públicos de la colección."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "slug": self.slug,
            "descripcion": self.descripcion,
            "imagen_url": self.imagen_url,
            "activa": self.activa,
            "orden": self.orden,
        }


class ColorProducto(db.Model):
    """Color disponible para una variante de producto."""

    __tablename__ = "colores_producto"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(60), nullable=False)
    codigo_hex = db.Column(db.String(7), nullable=False, default="#111827")
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    producto = db.relationship("Producto", back_populates="colores")


class Categoria(db.Model):
    """Representa una categoría usada para filtrar el catálogo."""

    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    productos = db.relationship("Producto", backref="categoria", lazy=True)

    def to_dict(self) -> dict:
        """Devuelve una representación pública de la categoría."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "slug": self.slug,
        }


class Etiqueta(db.Model):
    """Etiqueta productos con propiedades como «NUEVO» o «LIMITADO»."""

    __tablename__ = "etiquetas"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=False)

    def to_dict(self) -> dict:
        """Devuelve una representación básica de la etiqueta."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "slug": self.slug,
        }


class Producto(db.Model):
    """Información del producto y sus relaciones con imágenes y categorías."""

    __tablename__ = "productos"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    precio_usd = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    activo = db.Column(db.Boolean, default=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias.id"), nullable=False)
    imagenes = db.relationship(
        "ImagenProducto",
        backref="producto",
        cascade="all, delete-orphan",
        lazy=True,
    )
    etiquetas = db.relationship(
        "Etiqueta",
        secondary=producto_etiqueta,
        lazy="subquery",
        backref=db.backref("productos", lazy=True),
    )
    colores = db.relationship(
        "ColorProducto",
        back_populates="producto",
        cascade="all, delete-orphan",
        lazy=True,
    )

    def primary_image(self) -> str:
        """Devuelve la URL principal o un marcador si no existe una imagen."""
        for image in self.imagenes:
            if image.es_principal:
                return image.url_imagen
        return "/static/img/placeholder.svg"

    def to_dict(self) -> dict:
        """Devuelve una representación compatible con JSON para el catálogo y la API."""
        return {
            "id": self.id,
            "codigo": self.codigo,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "precio_usd": self.precio_usd,
            "stock": self.stock,
            "categoria": self.categoria.nombre if self.categoria else None,
            "categoria_id": self.categoria_id,
            "imagen": self.primary_image(),
            "slug": self.codigo.lower().replace(" ", "-"),
            "etiquetas": [etiqueta.nombre for etiqueta in self.etiquetas],
            "colores": [
                {"nombre": color.nombre, "codigo_hex": color.codigo_hex}
                for color in self.colores
            ],
        }


class ImagenProducto(db.Model):
    """Imagen asociada a un producto, incluida la imagen principal."""

    __tablename__ = "imagenes_producto"

    id = db.Column(db.Integer, primary_key=True)
    url_imagen = db.Column(db.String(255), nullable=False)
    es_principal = db.Column(db.Boolean, default=False)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)

    def to_dict(self) -> dict:
        """Devuelve los metadatos básicos para mostrar o serializar la imagen."""
        return {
            "id": self.id,
            "url_imagen": self.url_imagen,
            "es_principal": self.es_principal,
            "producto_id": self.producto_id,
        }
