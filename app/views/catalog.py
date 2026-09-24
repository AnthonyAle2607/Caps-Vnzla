"""Rutas del catálogo y storefront web de CAPS VNZLA."""

from __future__ import annotations

import json

from flask import Blueprint, current_app, jsonify, render_template, request

from app.models import Categoria, Producto

catalog_bp = Blueprint("catalog", __name__)


@catalog_bp.route("/")
def index() -> str:
    """Renderiza la página pública principal de la tienda.

    Entrega la estructura de la página y los productos en JSON para que el
    frontend los renderice dinámicamente con filtros, búsqueda y conversión.
    """
    categories = Categoria.query.order_by(Categoria.nombre).all()
    products = Producto.query.filter_by(activo=True).order_by(Producto.id).all()
    products_json = json.dumps([product.to_dict() for product in products])

    return render_template(
        "catalog/index.html",
        categories=categories,
        products=products,
        products_json=products_json,
        currency_rate=current_app.config["CURRENCY_RATE_BS"],
    )


@catalog_bp.route("/producto/<int:producto_id>")
def product_detail(producto_id: int) -> str:
    """Renderiza el detalle de un producto con descripción, precio y stock."""
    product = Producto.query.get_or_404(producto_id)
    return render_template(
        "catalog/product_detail.html",
        product=product,
        currency_rate=current_app.config["CURRENCY_RATE_BS"],
    )


@catalog_bp.route("/api/productos")
def get_productos():
    """Devuelve productos activos filtrados por categoría o texto."""
    categoria_id = request.args.get("categoria_id", type=int)
    busqueda = request.args.get("q", default="", type=str)

    query = Producto.query.filter_by(activo=True)

    if categoria_id:
        query = query.filter_by(categoria_id=categoria_id)

    if busqueda:
        query = query.filter(Producto.nombre.ilike(f"%{busqueda}%"))

    products = query.order_by(Producto.id).all()
    return jsonify([product.to_dict() for product in products])


@catalog_bp.route("/api/moneda")
def get_currency() -> tuple:
    """Expone la tasa de cambio al frontend sin fijarla directamente en JavaScript."""
    return jsonify({"bs_per_usd": current_app.config["CURRENCY_RATE_BS"]})
