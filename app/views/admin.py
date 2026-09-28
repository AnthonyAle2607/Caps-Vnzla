"""Rutas protegidas del panel administrativo de CAPS VNZLA."""

from __future__ import annotations

from functools import wraps
from io import BytesIO
import math
from datetime import datetime, timedelta
from pathlib import Path
import re
import unicodedata
from uuid import uuid4

import click
from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, session, url_for
from PIL import Image, UnidentifiedImageError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.models import (
    Administrador,
    Categoria,
    Coleccion,
    ColorProducto,
    ImagenProducto,
    MovimientoStock,
    Pedido,
    PedidoItem,
    Producto,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_PRODUCT_IMAGES = 8


@admin_bp.cli.command("list-users")
def list_users() -> None:
    """Lista usuarios administrativos sin mostrar información sensible."""
    admins = Administrador.query.order_by(Administrador.usuario).all()
    if not admins:
        click.echo("No hay usuarios administrativos.")
        return

    for admin in admins:
        status = "activo" if admin.activo else "inactivo"
        click.echo(f"{admin.usuario}\t{admin.rol}\t{status}")


@admin_bp.cli.command("reset-password")
@click.argument("usuario")
def reset_password(usuario: str) -> None:
    """Restablece la contraseña de un usuario desde la consola local."""
    admin = Administrador.query.filter_by(usuario=usuario).first()
    if admin is None:
        raise click.ClickException("No existe ese usuario administrativo.")

    password = click.prompt(
        "Nueva contraseña (mínimo 8 caracteres)",
        hide_input=True,
        confirmation_prompt=True,
    )
    if len(password) < 8:
        raise click.ClickException("La contraseña debe tener al menos 8 caracteres.")

    admin.password_hash = generate_password_hash(password)
    try:
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        raise click.ClickException("No se pudo actualizar la contraseña.") from error

    click.echo("Contraseña actualizada.")


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
        products=Producto.query.order_by(Producto.id.desc()).all(),
    )


@admin_bp.get("/ventas")
@requiere_permiso("ver_panel")
def sales_dashboard() -> str:
    """Resume pedidos, ingresos, margen conocido y necesidad de reposición."""
    period_options = {"7": 7, "30": 30, "90": 90}
    selected_period = request.args.get("periodo", "30")
    period_days = period_options.get(selected_period)
    if period_days is None:
        selected_period = "30"
        period_days = period_options[selected_period]

    today = datetime.utcnow().date()
    first_day = today - timedelta(days=period_days - 1)
    period_start = datetime.combine(first_day, datetime.min.time())
    lines = (
        PedidoItem.query.options(joinedload(PedidoItem.pedido))
        .join(Pedido, PedidoItem.pedido_id == Pedido.id)
        .filter(Pedido.creado_en >= period_start)
        .all()
    )
    sales_by_product: dict[int, dict] = {}
    sales_by_day: dict[str, dict] = {}
    known_cost_units = 0
    total_units = 0
    revenue_usd = 0.0
    known_cost_revenue_usd = 0.0
    gross_profit_usd = 0.0

    for offset in range(period_days):
        day = first_day + timedelta(days=offset)
        sales_by_day[day.isoformat()] = {"date": day, "revenue_usd": 0.0, "units": 0}

    for line in lines:
        item_revenue = line.precio_usd * line.cantidad
        revenue_usd += item_revenue
        total_units += line.cantidad
        day_key = line.pedido.creado_en.date().isoformat()
        if day_key in sales_by_day:
            sales_by_day[day_key]["revenue_usd"] += item_revenue
            sales_by_day[day_key]["units"] += line.cantidad

        metrics = sales_by_product.setdefault(
            line.producto_id,
            {
                "name": line.nombre_producto,
                "units": 0,
                "revenue_usd": 0.0,
                "known_cost_revenue_usd": 0.0,
                "profit_usd": 0.0,
                "known_cost_units": 0,
            },
        )
        metrics["units"] += line.cantidad
        metrics["revenue_usd"] += item_revenue
        if line.costo_usd is not None:
            item_profit = (line.precio_usd - line.costo_usd) * line.cantidad
            metrics["profit_usd"] += item_profit
            metrics["known_cost_revenue_usd"] += item_revenue
            metrics["known_cost_units"] += line.cantidad
            gross_profit_usd += item_profit
            known_cost_revenue_usd += item_revenue
            known_cost_units += line.cantidad

    product_rows = []
    for product in Producto.query.order_by(Producto.nombre).all():
        metrics = sales_by_product.get(
            product.id,
            {
                "name": product.nombre,
                "units": 0,
                "revenue_usd": 0.0,
                "known_cost_revenue_usd": 0.0,
                "profit_usd": 0.0,
                "known_cost_units": 0,
            },
        )
        metrics["product"] = product
        metrics["restock_suggestion"] = max(
            0,
            math.ceil(metrics["units"] / period_days * 30) - product.stock,
        )
        product_rows.append(metrics)

    profitable_products = sorted(
        (row for row in product_rows if row["units"] and row["known_cost_units"]),
        key=lambda row: (row["profit_usd"], row["units"]),
        reverse=True,
    )
    restock_products = sorted(
        (row for row in product_rows if row["restock_suggestion"] and row["product"].activo),
        key=lambda row: (row["restock_suggestion"], row["units"]),
        reverse=True,
    )
    daily_sales = list(sales_by_day.values())
    maximum_daily_revenue = max((day["revenue_usd"] for day in daily_sales), default=0)
    for day in daily_sales:
        day["bar_percent"] = (
            round(day["revenue_usd"] / maximum_daily_revenue * 100)
            if maximum_daily_revenue
            else 0
        )

    orders_count = Pedido.query.filter(Pedido.creado_en >= period_start).count()
    return render_template(
        "admin/sales_dashboard.html",
        selected_period=selected_period,
        period_days=period_days,
        order_count=orders_count,
        revenue_usd=revenue_usd,
        units_sold=total_units,
        gross_profit_usd=gross_profit_usd,
        margin_percent=(
            gross_profit_usd / known_cost_revenue_usd * 100
            if known_cost_revenue_usd
            else 0
        ),
        cost_coverage_percent=(known_cost_units / total_units * 100) if total_units else 0,
        unknown_cost_units=total_units - known_cost_units,
        sales_by_day=daily_sales,
        maximum_daily_revenue=maximum_daily_revenue,
        profitable_products=profitable_products[:8],
        restock_products=restock_products[:8],
        unsold_products_count=sum(row["units"] == 0 for row in product_rows),
    )


def _validar_imagenes(subidas, obligatorio: bool = False) -> list[tuple[bytes, str]]:
    """Valida tamaño y firma de cada imagen subida antes de guardarla."""
    archivos = [archivo for archivo in subidas if archivo and archivo.filename]
    if obligatorio and not archivos:
        raise ValueError("Selecciona al menos una imagen para el producto.")
    if len(archivos) > MAX_PRODUCT_IMAGES:
        raise ValueError(f"Puedes subir hasta {MAX_PRODUCT_IMAGES} imágenes por producto.")

    imagenes: list[tuple[bytes, str]] = []
    for archivo in archivos:
        contenido = archivo.stream.read(MAX_IMAGE_BYTES + 1)
        if len(contenido) > MAX_IMAGE_BYTES:
            raise ValueError("Cada imagen debe pesar como máximo 5 MB.")
        try:
            with Image.open(BytesIO(contenido)) as imagen:
                formato = imagen.format
                ancho, alto = imagen.size
                if ancho * alto > 40_000_000:
                    raise ValueError("La imagen no puede superar los 40 megapíxeles.")
                imagen.verify()
        except (OSError, UnidentifiedImageError, Image.DecompressionBombError):
            raise ValueError("Usa imágenes JPEG, PNG o WebP.") from None
        if formato not in {"JPEG", "PNG", "WEBP"}:
            raise ValueError("Usa imágenes JPEG, PNG o WebP.")
        extension = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}[formato]
        imagenes.append((contenido, extension))
    return imagenes


def _guardar_imagenes(imagenes: list[tuple[bytes, str]]) -> list[str]:
    """Guarda imágenes con nombres aleatorios y devuelve sus rutas públicas."""
    directorio = Path(current_app.static_folder) / "img" / "productos"
    directorio.mkdir(parents=True, exist_ok=True)
    rutas: list[str] = []
    try:
        for contenido, extension in imagenes:
            nombre = f"{uuid4().hex}{extension}"
            (directorio / nombre).write_bytes(contenido)
            rutas.append(f"/static/img/productos/{nombre}")
    except OSError:
        _limpiar_imagenes_subidas(rutas)
        raise
    return rutas


def _limpiar_imagenes_subidas(rutas: list[str]) -> None:
    """Retira únicamente los archivos nuevos cuando falla la operación."""
    directorio = (Path(current_app.static_folder) / "img" / "productos").resolve()
    for ruta in rutas:
        archivo = (Path(current_app.static_folder).parent / ruta.lstrip("/")).resolve()
        if archivo.parent == directorio:
            archivo.unlink(missing_ok=True)


def _eliminar_imagen_sin_referencias(ruta: str) -> None:
    """Elimina una foto administrada cuando ningún producto o colección la usa."""
    if not ruta.startswith("/static/img/productos/"):
        return
    usada_por_producto = ImagenProducto.query.filter_by(url_imagen=ruta).first()
    usada_por_coleccion = Coleccion.query.filter_by(imagen_url=ruta).first()
    if usada_por_producto or usada_por_coleccion:
        return
    archivo = (Path(current_app.static_folder).parent / ruta.lstrip("/")).resolve()
    directorio = (Path(current_app.static_folder) / "img" / "productos").resolve()
    if archivo.parent == directorio:
        archivo.unlink(missing_ok=True)


def _crear_slug(texto: str) -> str:
    """Normaliza un texto para usarlo como identificador legible de colección."""
    normalizado = unicodedata.normalize("NFKD", texto)
    sin_tildes = "".join(letra for letra in normalizado if not unicodedata.combining(letra))
    return re.sub(r"[^a-z0-9]+", "-", sin_tildes.lower()).strip("-")


def _datos_producto(formulario) -> dict:
    """Valida y normaliza los campos comerciales del formulario de producto."""
    codigo = formulario.get("codigo", "").strip().upper()
    nombre = formulario.get("nombre", "").strip()
    descripcion = formulario.get("descripcion", "").strip()
    if not codigo or len(codigo) > 50:
        raise ValueError("Indica un código de producto de hasta 50 caracteres.")
    if not nombre or len(nombre) > 150:
        raise ValueError("Indica un nombre de producto de hasta 150 caracteres.")
    if not descripcion:
        raise ValueError("La descripción del producto es obligatoria.")

    try:
        precio = float(formulario.get("precio_usd", ""))
        stock = int(formulario.get("stock", ""))
        categoria_id = int(formulario.get("categoria_id", ""))
        costo_texto = formulario.get("costo_usd", "").strip()
        costo = float(costo_texto) if costo_texto else None
    except (TypeError, ValueError):
        raise ValueError("Verifica el precio, el costo, el inventario y la categoría.") from None
    if (
        not math.isfinite(precio)
        or precio <= 0
        or stock < 0
        or (costo is not None and (not math.isfinite(costo) or costo <= 0))
    ):
        raise ValueError("El precio debe ser positivo, el costo debe ser positivo si se indica y el stock no puede ser negativo.")
    if db.session.get(Categoria, categoria_id) is None:
        raise ValueError("Selecciona una categoría válida.")
    return {
        "codigo": codigo,
        "nombre": nombre,
        "descripcion": descripcion,
        "precio_usd": precio,
        "costo_usd": costo,
        "stock": stock,
        "categoria_id": categoria_id,
        "activo": formulario.get("activo") == "on",
    }


def _colores_formulario(texto: str) -> list[tuple[str, str]]:
    """Interpreta colores con el formato «Nombre | #RRGGBB»."""
    colores: list[tuple[str, str]] = []
    nombres_vistos: set[str] = set()
    for linea in texto.splitlines():
        if not linea.strip():
            continue
        partes = linea.split("|", maxsplit=1)
        if len(partes) != 2:
            raise ValueError("Escribe cada color con el formato: Negro | #111111.")
        nombre, codigo_hex = (parte.strip() for parte in partes)
        if not nombre or not re.fullmatch(r"#[0-9a-fA-F]{6}", codigo_hex):
            raise ValueError("Cada color necesita un nombre y un código hexadecimal de 6 dígitos.")
        if nombre.casefold() in nombres_vistos:
            raise ValueError("No repitas nombres de colores en el mismo producto.")
        nombres_vistos.add(nombre.casefold())
        colores.append((nombre, codigo_hex.lower()))
    return colores


def _ids_seleccionados(nombre: str, modelo) -> list:
    """Valida los identificadores seleccionados en un control múltiple."""
    valores = request.form.getlist(nombre)
    try:
        identificadores = list(dict.fromkeys(int(valor) for valor in valores))
    except ValueError:
        raise ValueError("Una de las opciones seleccionadas no es válida.") from None
    existentes = modelo.query.filter(modelo.id.in_(identificadores)).all() if identificadores else []
    if len(existentes) != len(identificadores):
        raise ValueError("Una de las opciones seleccionadas ya no está disponible.")
    return existentes


def _mostrar_formulario_producto(product=None, form_data=None, error: str | None = None) -> str:
    """Renderiza el formulario compartido de alta y edición de productos."""
    return render_template(
        "admin/product_form.html",
        product=product,
        categories=Categoria.query.order_by(Categoria.nombre).all(),
        collections=Coleccion.query.order_by(Coleccion.orden, Coleccion.nombre).all(),
        form_data=form_data,
        error=error,
    )


@admin_bp.route("/productos/nuevo", methods=["GET", "POST"])
@requiere_permiso("editar_productos")
def create_product() -> str:
    """Crea un producto con imágenes, colores y colecciones seleccionadas."""
    if request.method == "GET":
        return _mostrar_formulario_producto()

    rutas_guardadas: list[str] = []
    try:
        datos = _datos_producto(request.form)
        if Producto.query.filter_by(codigo=datos["codigo"]).first():
            raise ValueError("Ya existe un producto con ese código.")
        colecciones = _ids_seleccionados("colecciones", Coleccion)
        colores = _colores_formulario(request.form.get("colores", ""))
        imagenes = _validar_imagenes(request.files.getlist("imagenes"), obligatorio=True)
        rutas_guardadas = _guardar_imagenes(imagenes)
        producto = Producto(**datos, colecciones=colecciones)
        db.session.add(producto)
        db.session.flush()
        db.session.add_all(
            [
                ImagenProducto(
                    url_imagen=ruta,
                    es_principal=indice == 0,
                    producto_id=producto.id,
                )
                for indice, ruta in enumerate(rutas_guardadas)
            ]
        )
        db.session.add_all(
            [
                ColorProducto(nombre=nombre, codigo_hex=codigo_hex, producto_id=producto.id)
                for nombre, codigo_hex in colores
            ]
        )
        if producto.stock:
            db.session.add(
                MovimientoStock(
                    producto_id=producto.id,
                    tipo="entrada",
                    cantidad=producto.stock,
                    stock_anterior=0,
                    stock_nuevo=producto.stock,
                    motivo="Inventario inicial al crear producto",
                )
            )
        db.session.commit()
    except ValueError as error:
        db.session.rollback()
        _limpiar_imagenes_subidas(rutas_guardadas)
        return _mostrar_formulario_producto(form_data=request.form, error=str(error))
    except (SQLAlchemyError, OSError):
        db.session.rollback()
        _limpiar_imagenes_subidas(rutas_guardadas)
        current_app.logger.exception("No se pudo crear el producto.")
        return _mostrar_formulario_producto(
            form_data=request.form,
            error="No se pudo guardar el producto. Verifica los datos e inténtalo de nuevo.",
        )

    flash("Producto creado correctamente.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/productos/<int:producto_id>/editar", methods=["GET", "POST"])
@requiere_permiso("editar_productos")
def edit_product(producto_id: int) -> str:
    """Edita el producto, sus imágenes, colores, colecciones e inventario."""
    product = Producto.query.get_or_404(producto_id)
    if request.method == "GET":
        return _mostrar_formulario_producto(product)

    rutas_guardadas: list[str] = []
    try:
        datos = _datos_producto(request.form)
        codigo_existente = Producto.query.filter(
            Producto.codigo == datos["codigo"],
            Producto.id != product.id,
        ).first()
        if codigo_existente:
            raise ValueError("Ya existe otro producto con ese código.")
        colecciones = _ids_seleccionados("colecciones", Coleccion)
        colores = _colores_formulario(request.form.get("colores", ""))
        archivos_nuevos = _validar_imagenes(request.files.getlist("imagenes"))
        imagenes_existentes = {imagen.id: imagen for imagen in product.imagenes}
        try:
            eliminar_ids = {
                int(identificador)
                for identificador in request.form.getlist("eliminar_imagenes")
            }
            imagen_principal_id = int(request.form.get("imagen_principal", ""))
        except ValueError:
            raise ValueError("Selecciona una imagen principal válida.") from None
        if not eliminar_ids.issubset(imagenes_existentes):
            raise ValueError("No se puede retirar una imagen que no pertenece al producto.")

        imagenes_conservadas = {
            identificador: imagen
            for identificador, imagen in imagenes_existentes.items()
            if identificador not in eliminar_ids
        }
        if archivos_nuevos:
            imagen_principal_id = 0
        elif imagen_principal_id not in imagenes_conservadas:
            raise ValueError("Conserva al menos una imagen y selecciona cuál será la portada.")
        if len(imagenes_conservadas) + len(archivos_nuevos) > MAX_PRODUCT_IMAGES:
            raise ValueError(f"Un producto puede tener hasta {MAX_PRODUCT_IMAGES} imágenes.")
        if not imagenes_conservadas and not archivos_nuevos:
            raise ValueError("Conserva o sube al menos una imagen para el producto.")

        rutas_eliminadas = [
            imagenes_existentes[identificador].url_imagen
            for identificador in eliminar_ids
        ]
        rutas_guardadas = _guardar_imagenes(archivos_nuevos)
        stock_anterior = product.stock
        for clave, valor in datos.items():
            setattr(product, clave, valor)
        product.colecciones = colecciones
        product.colores.clear()
        product.colores.extend(
            [
                ColorProducto(nombre=nombre, codigo_hex=codigo_hex)
                for nombre, codigo_hex in colores
            ]
        )
        for identificador in eliminar_ids:
            db.session.delete(imagenes_existentes[identificador])
        for identificador, imagen in imagenes_conservadas.items():
            imagen.es_principal = identificador == imagen_principal_id
        for indice, ruta in enumerate(rutas_guardadas):
            db.session.add(
                ImagenProducto(
                    url_imagen=ruta,
                    es_principal=indice == 0 and bool(archivos_nuevos),
                    producto_id=product.id,
                )
            )
        if datos["stock"] != stock_anterior:
            db.session.add(
                MovimientoStock(
                    producto_id=product.id,
                    tipo="ajuste",
                    cantidad=abs(datos["stock"] - stock_anterior),
                    stock_anterior=stock_anterior,
                    stock_nuevo=datos["stock"],
                    motivo="Ajuste manual desde administración",
                )
            )
        db.session.commit()
    except ValueError as error:
        db.session.rollback()
        _limpiar_imagenes_subidas(rutas_guardadas)
        return _mostrar_formulario_producto(
            product=product,
            form_data=request.form,
            error=str(error),
        )
    except (SQLAlchemyError, OSError):
        db.session.rollback()
        _limpiar_imagenes_subidas(rutas_guardadas)
        current_app.logger.exception("No se pudo actualizar el producto %s.", producto_id)
        return _mostrar_formulario_producto(
            product=product,
            form_data=request.form,
            error="No se pudo guardar el producto. Verifica los datos e inténtalo de nuevo.",
        )

    for ruta in rutas_eliminadas:
        _eliminar_imagen_sin_referencias(ruta)
    flash("Producto actualizado correctamente.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.post("/productos/<int:producto_id>/estado")
@requiere_permiso("editar_productos")
def toggle_product_status(producto_id: int):
    """Publica o retira un producto sin borrar su historial de pedidos."""
    product = Producto.query.get_or_404(producto_id)
    product.activo = not product.activo
    db.session.commit()
    flash(
        "Producto publicado en la tienda." if product.activo else "Producto retirado del catálogo.",
        "success",
    )
    return redirect(url_for("admin.dashboard"))


@admin_bp.get("/colecciones")
@requiere_permiso("editar_productos")
def manage_collections() -> str:
    """Lista las colecciones existentes y permite administrar su contenido."""
    collections = Coleccion.query.order_by(Coleccion.orden, Coleccion.nombre).all()
    return render_template("admin/collections.html", collections=collections)


@admin_bp.route("/colecciones/nueva", methods=["GET", "POST"])
@admin_bp.route("/colecciones/<int:coleccion_id>/editar", methods=["GET", "POST"])
@requiere_permiso("editar_productos")
def edit_collection(coleccion_id: int | None = None) -> str:
    """Crea o actualiza una colección con portada y productos asignados."""
    collection = db.session.get(Coleccion, coleccion_id) if coleccion_id is not None else None
    if coleccion_id is not None and collection is None:
        abort(404)

    if request.method == "GET":
        return render_template(
            "admin/edit_collection.html",
            collection=collection,
            products=Producto.query.order_by(Producto.nombre).all(),
            form_data=None,
            error=None,
        )

    rutas_guardadas: list[str] = []
    ruta_anterior = collection.imagen_url if collection else None
    try:
        nombre = request.form.get("nombre", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        try:
            orden = int(request.form.get("orden", "0"))
        except ValueError:
            raise ValueError("El orden de la colección debe ser un número entero.") from None
        if not nombre or len(nombre) > 120 or not descripcion:
            raise ValueError("Completa un nombre válido y la descripción de la colección.")
        if orden < 0:
            raise ValueError("El orden de la colección no puede ser negativo.")
        slug_base = _crear_slug(nombre)
        if not slug_base:
            raise ValueError("El nombre debe incluir letras o números.")
        slug = slug_base
        sufijo = 2
        while Coleccion.query.filter(Coleccion.slug == slug, Coleccion.id != (collection.id if collection else 0)).first():
            slug = f"{slug_base}-{sufijo}"
            sufijo += 1
        productos = _ids_seleccionados("productos", Producto)
        archivos = _validar_imagenes(request.files.getlist("imagen"), obligatorio=collection is None)
        if len(archivos) > 1:
            raise ValueError("Selecciona una sola imagen para la portada de la colección.")
        rutas_guardadas = _guardar_imagenes(archivos)
        if collection is None:
            collection = Coleccion(
                nombre=nombre,
                slug=slug,
                descripcion=descripcion,
                imagen_url=rutas_guardadas[0],
                activa=request.form.get("activa") == "on",
                orden=orden,
                productos=productos,
            )
            db.session.add(collection)
        else:
            collection.nombre = nombre
            collection.slug = slug
            collection.descripcion = descripcion
            collection.orden = orden
            collection.activa = request.form.get("activa") == "on"
            collection.productos = productos
            if rutas_guardadas:
                collection.imagen_url = rutas_guardadas[0]
        db.session.commit()
    except ValueError as error:
        db.session.rollback()
        _limpiar_imagenes_subidas(rutas_guardadas)
        return render_template(
            "admin/edit_collection.html",
            collection=collection,
            products=Producto.query.order_by(Producto.nombre).all(),
            form_data=request.form,
            error=str(error),
        )
    except (SQLAlchemyError, OSError):
        db.session.rollback()
        _limpiar_imagenes_subidas(rutas_guardadas)
        current_app.logger.exception("No se pudo guardar la colección.")
        return render_template(
            "admin/edit_collection.html",
            collection=collection,
            products=Producto.query.order_by(Producto.nombre).all(),
            form_data=request.form,
            error="No se pudo guardar la colección. Verifica los datos e inténtalo de nuevo.",
        )

    if rutas_guardadas and ruta_anterior and ruta_anterior != rutas_guardadas[0]:
        _eliminar_imagen_sin_referencias(ruta_anterior)
    flash("Colección guardada correctamente.", "success")
    return redirect(url_for("admin.manage_collections"))


@admin_bp.post("/colecciones/<int:coleccion_id>/estado")
@requiere_permiso("editar_productos")
def toggle_collection_status(coleccion_id: int):
    """Activa o retira una colección sin perder sus productos asignados."""
    collection = Coleccion.query.get_or_404(coleccion_id)
    collection.activa = not collection.activa
    db.session.commit()
    flash(
        "Colección publicada en la tienda." if collection.activa else "Colección retirada de la tienda.",
        "success",
    )
    return redirect(url_for("admin.manage_collections"))


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
