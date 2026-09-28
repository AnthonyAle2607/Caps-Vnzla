"""Guardar costos unitarios para analizar la rentabilidad de ventas.

Revision ID: 76b9c0e15a43
Revises: 4d20a6e6bb31
"""

from alembic import op
import sqlalchemy as sa


revision = "76b9c0e15a43"
down_revision = "4d20a6e6bb31"
branch_labels = None
depends_on = None


def upgrade():
    """Agrega el costo de compra y lo congela en futuras líneas de pedido."""
    columnas_producto = {
        columna["name"]
        for columna in sa.inspect(op.get_bind()).get_columns("productos")
    }
    if "costo_usd" not in columnas_producto:
        op.add_column("productos", sa.Column("costo_usd", sa.Float(), nullable=True))

    columnas_pedido = {
        columna["name"]
        for columna in sa.inspect(op.get_bind()).get_columns("pedido_items")
    }
    if "costo_usd" not in columnas_pedido:
        op.add_column(
            "pedido_items",
            sa.Column("costo_usd", sa.Float(), nullable=True),
        )


def downgrade():
    """Elimina los costos capturados si se revierte el análisis de rentabilidad."""
    columnas_pedido = {
        columna["name"]
        for columna in sa.inspect(op.get_bind()).get_columns("pedido_items")
    }
    if "costo_usd" in columnas_pedido:
        op.drop_column("pedido_items", "costo_usd")

    columnas_producto = {
        columna["name"]
        for columna in sa.inspect(op.get_bind()).get_columns("productos")
    }
    if "costo_usd" in columnas_producto:
        op.drop_column("productos", "costo_usd")
