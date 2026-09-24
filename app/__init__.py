"""Fábrica de aplicación Flask para el catálogo de CAPS VNZLA."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from app.config import Config

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Instancias compartidas de base de datos y migraciones usadas por la aplicación.
db = SQLAlchemy()
migrate = Migrate()


def create_app() -> Flask:
    """Crea y configura la aplicación Flask.

    La fábrica centraliza la configuración, permite pruebas con ajustes
    personalizados y garantiza que el esquema exista antes de atender solicitudes.
    """
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    # Mantiene las variables de entorno sincronizadas con la configuración activa.
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", app.config["SECRET_KEY"])
    app.config["CURRENCY_RATE_BS"] = float(
        os.getenv("CURRENCY_RATE_BS", app.config["CURRENCY_RATE_BS"])
    )

    db.init_app(app)
    migrate.init_app(app, db)

    from app.views.catalog import catalog_bp

    app.register_blueprint(catalog_bp)

    with app.app_context():
        db.create_all()
        seed_data()

    return app


def seed_data() -> None:
    """Carga datos iniciales cuando la base de datos aún no tiene catálogo."""
    from app.models import Categoria, ImagenProducto, Producto

    if Categoria.query.first() is not None:
        return

    categorias = [
        Categoria(nombre="Urban", slug="urban"),
        Categoria(nombre="Classic", slug="classic"),
        Categoria(nombre="Team", slug="team"),
    ]
    db.session.add_all(categorias)
    db.session.commit()

    products = [
        {
            "codigo": "CAP-001",
            "nombre": "Street Rush",
            "descripcion": "Gorra urbana con diseño sobrio, estructura rígida y acabado premium para uso diario.",
            "precio_usd": 29.99,
            "stock": 18,
            "categoria_id": 1,
            "imagenes": [
                ("https://images.unsplash.com/photo-1521369909026-2afc912d5f37?auto=format&fit=crop&w=900&q=80", True),
                ("https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=900&q=80", False),
            ],
        },
        {
            "codigo": "CAP-002",
            "nombre": "Night Classic",
            "descripcion": "Línea clásica con color negro y detalle amarillo para un look elegante y minimalista.",
            "precio_usd": 32.50,
            "stock": 12,
            "categoria_id": 2,
            "imagenes": [
                ("https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=900&q=80", True),
                ("https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=900&q=80", False),
            ],
        },
        {
            "codigo": "CAP-003",
            "nombre": "Vibe Team",
            "descripcion": "Diseño deportivo y resistente con estética de club, ideal para fanáticos del streetwear.",
            "precio_usd": 35.00,
            "stock": 9,
            "categoria_id": 3,
            "imagenes": [
                ("https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=900&q=80", True),
                ("https://images.unsplash.com/photo-1496747611176-843222e1e57c?auto=format&fit=crop&w=900&q=80", False),
            ],
        },
        {
            "codigo": "CAP-004",
            "nombre": "Volt Edge",
            "descripcion": "Detalle premium con contraste amarillo intenso para un look moderno y llamativo.",
            "precio_usd": 39.90,
            "stock": 7,
            "categoria_id": 1,
            "imagenes": [
                ("https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=900&q=80", True),
                ("https://images.unsplash.com/photo-1504593811423-6dd665756598?auto=format&fit=crop&w=900&q=80", False),
            ],
        },
    ]

    for product_data in products:
        product = Producto(
            codigo=product_data["codigo"],
            nombre=product_data["nombre"],
            descripcion=product_data["descripcion"],
            precio_usd=product_data["precio_usd"],
            stock=product_data["stock"],
            categoria_id=product_data["categoria_id"],
            activo=True,
        )
        db.session.add(product)
        db.session.flush()

        for image_url, is_primary in product_data["imagenes"]:
            db.session.add(
                ImagenProducto(
                    url_imagen=image_url,
                    es_principal=is_primary,
                    producto_id=product.id,
                )
            )

    db.session.commit()
