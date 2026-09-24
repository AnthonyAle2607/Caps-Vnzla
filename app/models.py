"""Database models for the CAPS VNZLA catalog."""

from __future__ import annotations

from app import db

producto_etiqueta = db.Table(
    "producto_etiqueta",
    db.Column("producto_id", db.Integer, db.ForeignKey("productos.id"), primary_key=True),
    db.Column("etiqueta_id", db.Integer, db.ForeignKey("etiquetas.id"), primary_key=True),
)


class Categoria(db.Model):
    """Represents a product category used to filter the catalog."""

    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    productos = db.relationship("Producto", backref="categoria", lazy=True)

    def to_dict(self) -> dict:
        """Return a public representation of the category."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "slug": self.slug,
        }


class Etiqueta(db.Model):
    """Label used to tag products with properties such as "NUEVO" or "LIMITADO"."""

    __tablename__ = "etiquetas"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=False)

    def to_dict(self) -> dict:
        """Return a basic dictionary representation of the label."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "slug": self.slug,
        }


class Producto(db.Model):
    """Catalog product information and its relationship with images and categories."""

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

    def primary_image(self) -> str:
        """Return the primary image URL or a placeholder if not defined."""
        for image in self.imagenes:
            if image.es_principal:
                return image.url_imagen
        return "/static/img/placeholder.svg"

    def to_dict(self) -> dict:
        """Return a JSON-safe representation for the catalog and API."""
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
        }


class ImagenProducto(db.Model):
    """Image associated with a product, including the preferred main image."""

    __tablename__ = "imagenes_producto"

    id = db.Column(db.Integer, primary_key=True)
    url_imagen = db.Column(db.String(255), nullable=False)
    es_principal = db.Column(db.Boolean, default=False)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)

    def to_dict(self) -> dict:
        """Return the basic image metadata for display or serialization."""
        return {
            "id": self.id,
            "url_imagen": self.url_imagen,
            "es_principal": self.es_principal,
            "producto_id": self.producto_id,
        }
