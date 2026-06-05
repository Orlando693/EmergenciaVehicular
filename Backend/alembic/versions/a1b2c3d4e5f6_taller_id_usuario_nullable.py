"""taller id_usuario nullable y sin unique global

Revision ID: a1b2c3d4e5f6
Revises: f10a2b3c4d5e
Create Date: 2026-06-04

Permite que un ADMINISTRADOR registre talleres sin necesitar un usuario
propietario. La unicidad de id_usuario se mantiene sólo como índice parcial
(WHERE id_usuario IS NOT NULL) para que cada usuario-taller siga teniendo
máximo un taller, pero el ADMIN pueda crear talleres "sin dueño".
"""
from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "f10a2b3c4d5e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Eliminar la restricción unique global sobre id_usuario
    op.drop_constraint("talleres_id_usuario_key", "talleres", type_="unique")

    # 2. Hacer la columna nullable y cambiar ondelete a SET NULL
    op.alter_column(
        "talleres",
        "id_usuario",
        existing_type=sa.BigInteger(),
        nullable=True,
    )

    # 3. Crear índice único parcial: sólo se aplica cuando id_usuario NO es NULL
    op.create_index(
        "uq_talleres_id_usuario_notnull",
        "talleres",
        ["id_usuario"],
        unique=True,
        postgresql_where=sa.text("id_usuario IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_talleres_id_usuario_notnull", table_name="talleres")
    op.alter_column(
        "talleres",
        "id_usuario",
        existing_type=sa.BigInteger(),
        nullable=False,
    )
    op.create_unique_constraint("talleres_id_usuario_key", "talleres", ["id_usuario"])
