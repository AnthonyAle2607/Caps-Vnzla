"""Rutas protegidas del panel administrativo de CAPS VNZLA."""

from __future__ import annotations

from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from app import db
from app.models import Administrador, Categoria, Coleccion, MovimientoStock, Pedido, Producto

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def administrador_actual() -> Administrador | None:
    """Obtiene el administrador autenticado desde la sesión."""
    admin_id = session.get("admin_id")
    return Administrador.query.get(admin_id) if admin_id else None


def requiere_permiso(permiso: str):
    """Protege una ruta según el permiso requerido por el rol."""
    def decorador(funcion):
        @wraps(funcion)
        def envoltura(*args, **kwargs):
            admin = administrador_actual()
            if admin is None:
                return redirect(url_for("admin.login", next=request.path))
            if not admin.tiene_permiso(permiso):
                flash("No tienes permisos para realizar esta acción.", "error")
                return redirect(url_for("admin.dashboard"))
            return funcion(*args, **kwargs)
        return envoltura
    return decorador


@admin_bp.route("/login", methods=["GET", "POST"])
def login() -> str:
    """Autentica un administrador mediante usuario y contraseña."""
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        password = request.form.get("password", "")
        admin = Administrador.query.filter_by(usuario=usuario, activo=True).first()
        if admin and check_password_hash(admin.password_hash, password):
            session["admin_id"] = admin.id
            return redirect(request.args.get("next") or url_for("admin.dashboard"))
        flash("Usuario o contraseña incorrectos.", "error")
    return render_template("admin/login.html")


@admin_bp.get("/logout")
def logout():
    """Cierra la sesión administrativa actual."""
    session.pop("admin_id", None)
    return redirect(url_for("admin.login"))


@admin_bp.get("/")
@requiere_permiso("ver_panel")
def dashboard() -> str:
    """Renderiza el resumen administrativo."""
    return render_template(
        "admin/dashboard.html",
        admin=administrador_actual(),
        product_count=Producto.query.count(),
        active_product_count=Producto.query.filter_by(activo=True).count(),
        category_count=Categoria.query.count(),
        collection_count=Coleccion.query.filter_by(activa=True).count(),
        order_count=Pedido.query.count(),
        orders=Pedido.query.order_by(Pedido.creado_en.desc()).limit(8).all(),
        products=Producto.query.order_by(Producto.id.desc()).limit(8).all(),
    )


@admin_bp.route("/productos/<int:producto_id>/editar", methods=["GET", "POST"])
@requiere_permiso("editar_productos")
def edit_product(producto_id: int) -> str:
    """Edita los datos comerciales y registra cualquier ajuste de stock."""
    product = Producto.query.get_or_404(producto_id)
    categories = Categoria.query.order_by(Categoria.nombre).all()
    if request.method == "POST":
        try:
            new_stock = int(request.form.get("stock", "0"))
            new_price = float(request.form.get("precio_usd", "0"))
            if new_stock < 0 or new_price < 0:
                raise ValueError
        except ValueError:
            flash("El precio y el stock deben ser valores válidos no negativos.", "error")
            return render_template("admin/edit_product.html", product=product, categories=categories)

        previous_stock = product.stock
        product.nombre = request.form.get("nombre", "").strip()
        product.descripcion = request.form.get("descripcion", "").strip()
        product.precio_usd = new_price
        product.stock = new_stock
        product.categoria_id = int(request.form.get("categoria_id", product.categoria_id))
        product.activo = request.form.get("activo") == "on"
        if new_stock != previous_stock:
            db.session.add(
                MovimientoStock(
                    producto_id=product.id,
                    tipo="ajuste",
                    cantidad=abs(new_stock - previous_stock),
                    stock_anterior=previous_stock,
                    stock_nuevo=new_stock,
                    motivo="Ajuste manual desde administración",
                )
            )
        db.session.commit()
        flash("Producto actualizado correctamente.", "success")
        return redirect(url_for("admin.dashboard"))
    return render_template("admin/edit_product.html", product=product, categories=categories)


@admin_bp.get("/movimientos")
@requiere_permiso("ver_panel")
def stock_movements() -> str:
    """Muestra el historial de movimientos de inventario."""
    movements = MovimientoStock.query.order_by(MovimientoStock.creado_en.desc()).limit(100).all()
    return render_template("admin/stock_movements.html", movements=movements)


@admin_bp.get("/pedidos")
@requiere_permiso("ver_panel")
def orders() -> str:
    """Muestra los pedidos registrados por los clientes."""
    orders = Pedido.query.order_by(Pedido.creado_en.desc()).limit(100).all()
    return render_template("admin/orders.html", orders=orders)
