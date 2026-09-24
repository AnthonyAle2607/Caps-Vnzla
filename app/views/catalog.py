"""Catalog and storefront routes for the CAPS VNZLA web app."""

from __future__ import annotations

import json

from flask import Blueprint, current_app, jsonify, render_template, request

from app.models import Categoria, Producto

catalog_bp = Blueprint("catalog", __name__)


@catalog_bp.route("/")
def index() -> str:
    """Render the public storefront home page.

    Returns the page shell plus the product list in JSON form so the frontend can
    render it dynamically with filters, search and currency conversion.
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
    """Render a product detail page with description, pricing and stock."""
    product = Producto.query.get_or_404(producto_id)
    return render_template(
        "catalog/product_detail.html",
        product=product,
        currency_rate=current_app.config["CURRENCY_RATE_BS"],
    )


@catalog_bp.route("/api/productos")
def get_productos():
    """Return a JSON list of active products filtered by category or text query."""
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
    """Expose the exchange rate to the frontend without hardcoding it in JS."""
    return jsonify({"bs_per_usd": current_app.config["CURRENCY_RATE_BS"]})
