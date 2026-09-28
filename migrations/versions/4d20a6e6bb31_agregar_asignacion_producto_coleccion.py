"""Agregar la relación entre productos y colecciones.

Revision ID: 4d20a6e6bb31
Revises: 9c5417157517
"""

from alembic import op
import sqlalchemy as sa


revision = "4d20a6e6bb31"
down_revision = "9c5417157517"
branch_labels = None
depends_on = None


def upgrade():
    """Crea la relación y asigna los productos de demostración existentes."""
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("producto_coleccion"):
        op.create_table(
            "producto_coleccion",
            sa.Column("producto_id", sa.Integer(), nullable=False),
            sa.Column("coleccion_id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["coleccion_id"], ["colecciones.id"]),
            sa.ForeignKeyConstraint(["producto_id"], ["productos.id"]),
            sa.PrimaryKeyConstraint("producto_id", "coleccion_id"),
        )

    if not any(
        indice["name"] == "ix_producto_coleccion_coleccion_id"
        for indice in inspector.get_indexes("producto_coleccion")
    ):
        op.create_index(
            "ix_producto_coleccion_coleccion_id",
            "producto_coleccion",
            ["coleccion_id"],
        )

    productos = sa.table(
        "productos",
        sa.column("id", sa.Integer()),
        sa.column("categoria_id", sa.Integer()),
    )
    categorias = sa.table(
        "categorias",
        sa.column("id", sa.Integer()),
        sa.column("slug", sa.String()),
    )
    colecciones = sa.table(
        "colecciones",
        sa.column("id", sa.Integer()),
        sa.column("slug", sa.String()),
    )
    asignaciones = sa.table(
        "producto_coleccion",
        sa.column("producto_id", sa.Integer()),
        sa.column("coleccion_id", sa.Integer()),
    )
    slug_coleccion = sa.case(
        (categorias.c.slug == "urban", "urban-essentials"),
        (categorias.c.slug == "classic", "classic-black"),
        (categorias.c.slug == "team", "team-spirit"),
        else_=None,
    )
    productos_por_coleccion = (
        sa.select(productos.c.id, colecciones.c.id)
        .select_from(
            productos.join(categorias, productos.c.categoria_id == categorias.c.id).join(
                colecciones,
                colecciones.c.slug == slug_coleccion,
            )
        )
        .where(
            ~sa.exists(
                sa.select(asignaciones.c.producto_id).where(
                    sa.and_(
                        asignaciones.c.producto_id == productos.c.id,
                        asignaciones.c.coleccion_id == colecciones.c.id,
                    )
                )
            )
        )
    )
    op.execute(
        sa.insert(asignaciones).from_select(
            ["producto_id", "coleccion_id"],
            productos_por_coleccion,
        )
    )


def downgrade():
    """Retira la relación producto-colección creada por esta revisión."""
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table("producto_coleccion"):
        indices = {indice["name"] for indice in inspector.get_indexes("producto_coleccion")}
        if "ix_producto_coleccion_coleccion_id" in indices:
            op.drop_index(
                "ix_producto_coleccion_coleccion_id",
                table_name="producto_coleccion",
            )
        op.drop_table("producto_coleccion")
