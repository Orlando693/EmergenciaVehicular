"""Add CU20 repair quotations

Revision ID: d20b8f1a6c33
Revises: c19a7e4d2b10
Create Date: 2026-05-28 19:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d20b8f1a6c33"
down_revision: Union[str, None] = "c19a7e4d2b10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _tables() -> set[str]:
    bind = op.get_bind()
    return set(sa.inspect(bind).get_table_names())


def upgrade() -> None:
    existing = _tables()
    if "cotizaciones_reparacion" in existing:
        return

    op.create_table(
        "cotizaciones_reparacion",
        sa.Column("id_cotizacion", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("id_tenant", sa.BigInteger(), nullable=False),
        sa.Column("id_incidente", sa.BigInteger(), nullable=False),
        sa.Column("id_cliente", sa.BigInteger(), nullable=False),
        sa.Column("id_taller", sa.BigInteger(), nullable=False),
        sa.Column("descripcion_solicitud", sa.String(length=500), nullable=True),
        sa.Column("estado", sa.String(length=30), nullable=False, server_default="PENDIENTE"),
        sa.Column("precio_estimado", sa.Numeric(12, 2), nullable=True),
        sa.Column("detalle_danio", sa.String(length=1000), nullable=True),
        sa.Column("condiciones_servicio", sa.String(length=1000), nullable=True),
        sa.Column("tiempo_estimado", sa.String(length=100), nullable=True),
        sa.Column("respuesta_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["id_tenant"], ["tenants.id_tenant"], name="fk_cotizaciones_tenant"),
        sa.ForeignKeyConstraint(["id_incidente"], ["incidentes.id_incidente"], name="fk_cotizaciones_incidente", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["id_cliente"], ["clientes.id_cliente"], name="fk_cotizaciones_cliente", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["id_taller"], ["talleres.id_taller"], name="fk_cotizaciones_taller", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id_cotizacion"),
        sa.UniqueConstraint("id_tenant", "id_incidente", "id_taller", name="uq_cotizacion_tenant_incidente_taller"),
    )
    op.create_index("ix_cotizaciones_tenant_cliente", "cotizaciones_reparacion", ["id_tenant", "id_cliente"])
    op.create_index("ix_cotizaciones_tenant_taller", "cotizaciones_reparacion", ["id_tenant", "id_taller"])
    op.create_index("ix_cotizaciones_tenant_incidente", "cotizaciones_reparacion", ["id_tenant", "id_incidente"])


def downgrade() -> None:
    existing = _tables()
    if "cotizaciones_reparacion" not in existing:
        return

    op.drop_index("ix_cotizaciones_tenant_incidente", table_name="cotizaciones_reparacion")
    op.drop_index("ix_cotizaciones_tenant_taller", table_name="cotizaciones_reparacion")
    op.drop_index("ix_cotizaciones_tenant_cliente", table_name="cotizaciones_reparacion")
    op.drop_table("cotizaciones_reparacion")
