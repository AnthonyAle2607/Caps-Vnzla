"""Rutas del catálogo y storefront web de CAPS VNZLA."""

from __future__ import annotations

import json
from urllib.parse import quote

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for

from app import db
from app.models import Categoria, Coleccion, MovimientoStock, Pedido, PedidoItem, Producto

catalog_bp = Blueprint("catalog", __name__)
WHATSAPP_MESSAGE_LIMIT = 2000


@catalog_bp.route("/")
def index() -> str:
    """Renderiza la página pública principal de la tienda.

    Entrega la estructura de la página y los productos en JSON para que el
    frontend los renderice dinámicamente con filtros, búsqueda y conversión.
    """
    categories = Categoria.query.order_by(Categoria.nombre).all()
    products = Producto.query.filter_by(activo=True).order_by(Producto.id).all()
    collections = Coleccion.query.filter_by(activa=True).order_by(Coleccion.orden).all()
    products_json = json.dumps([product.to_dict() for product in products])

    return render_template(
        "catalog/index.html",
        categories=categories,
        products=products,
        products_json=products_json,
        collections=collections,
        currency_rate=current_app.config["CURRENCY_RATE_BS"],
    )


@catalog_bp.route("/producto/<int:producto_id>")
def product_detail(producto_id: int) -> str:
    """Renderiza el detalle de un producto con descripción, precio y stock."""
    product = Producto.query.get_or_404(producto_id)
    recommendations = (
        Producto.query.filter(
            Producto.activo.is_(True),
            Producto.id != product.id,
            Producto.categoria_id == product.categoria_id,
        )
        .order_by(Producto.id)
        .limit(4)
        .all()
    )
    if len(recommendations) < 4:
        extra_recommendations = (
            Producto.query.filter(
                Producto.activo.is_(True),
                Producto.id != product.id,
                Producto.categoria_id != product.categoria_id,
            )
            .order_by(Producto.id)
            .limit(4 - len(recommendations))
            .all()
        )
        recommendations.extend(extra_recommendations)
    return render_template(
        "catalog/product_detail.html",
        product=product,
        recommendations=recommendations,
        currency_rate=current_app.config["CURRENCY_RATE_BS"],
        shipping_cost=current_app.config["SHIPPING_COST_USD"],
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


@catalog_bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    """Recibe los datos del comprador, registra el pedido y abre WhatsApp."""
    if request.method == "GET":
        return render_template(
            "catalog/checkout.html",
            currency_rate=current_app.config["CURRENCY_RATE_BS"],
            shipping_cost=current_app.config["SHIPPING_COST_USD"],
        )

    try:
        customer = {
            "nombre_cliente": request.form.get("nombre_cliente", "").strip(),
            "telefono": request.form.get("telefono", "").strip(),
            "correo": request.form.get("correo", "").strip(),
            "direccion": request.form.get("direccion", "").strip(),
            "referencia": request.form.get("referencia", "").strip(),
        }
        if not all(customer[key] for key in ("nombre_cliente", "telefono", "correo", "direccion")):
            raise ValueError("Completa todos los datos obligatorios.")
        cart = json.loads(request.form.get("cart", "[]"))
        if not isinstance(cart, list) or not cart:
            raise ValueError("El carrito está vacío.")
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        flash(str(error), "error")
        return redirect(url_for("catalog.checkout"))

    pedido = Pedido(**customer, total_usd=0)
    db.session.add(pedido)
    db.session.flush()
    total_usd = 0.0
    message_items = []
    for cart_item in cart:
        product = Producto.query.get(int(cart_item.get("id", 0)))
        quantity = int(cart_item.get("quantity", 0))
        if product is None or quantity <= 0 or not product.activo:
            db.session.rollback()
            flash("Uno de los productos del carrito ya no está disponible.", "error")
            return redirect(url_for("catalog.checkout"))
        if quantity > product.stock:
            db.session.rollback()
            flash(f"No hay suficiente stock de {product.nombre}.", "error")
            return redirect(url_for("catalog.checkout"))
        line_total = product.precio_usd * quantity
        total_usd += line_total
        pedido.items.append(
            PedidoItem(
                producto_id=product.id,
                nombre_producto=product.nombre,
                precio_usd=product.precio_usd,
                cantidad=quantity,
            )
        )
        previous_stock = product.stock
        product.stock -= quantity
        db.session.add(
            MovimientoStock(
                producto_id=product.id,
                tipo="salida",
                cantidad=quantity,
                stock_anterior=previous_stock,
                stock_nuevo=product.stock,
                motivo="Pedido enviado por WhatsApp",
                pedido_id=pedido.id,
            )
        )
        message_items.append(f"- {product.nombre} x{quantity}: ${line_total:.2f}")

    shipping_cost = current_app.config["SHIPPING_COST_USD"]
    pedido.total_usd = total_usd + shipping_cost
    db.session.commit()

    message = (
        f"Hola CAPS VNZLA, quiero confirmar el pedido #{pedido.id}.%0A"
        f"Cliente: {customer['nombre_cliente']}%0A"
        f"Teléfono: {customer['telefono']}%0A"
        f"Correo: {customer['correo']}%0A"
        f"Dirección: {customer['direccion']}%0A"
        f"Referencia: {customer['referencia'] or 'N/A'}%0A%0A"
        + "%0A".join(message_items)
        + f"%0AEnvío: ${shipping_cost:.2f}"
        + f"%0ATotal USD: ${pedido.total_usd:.2f}"
    )
    message = quote(message, safe="%")
    whatsapp_url = f"https://wa.me/{current_app.config['WHATSAPP_PHONE']}?text={message}"
    return render_template("catalog/checkout_success.html", pedido=pedido, whatsapp_url=whatsapp_url)
