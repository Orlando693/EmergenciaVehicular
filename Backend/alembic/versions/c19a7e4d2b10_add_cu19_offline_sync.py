"""Add CU19 offline emergency sync

Revision ID: c19a7e4d2b10
Revises: b6f4d2a1c9e8
Create Date: 2026-05-28 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c19a7e4d2b10"
down_revision: Union[str, None] = "b6f4d2a1c9e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _tables() -> set[str]:
    bind = op.get_bind()
    return set(sa.inspect(bind).get_table_names())


def upgrade() -> None:
    existing = _tables()
    if "emergencias_offline_sync" in existing:
        return

    op.create_table(
        "emergencias_offline_sync",
        sa.Column("id_sync", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("id_tenant", sa.BigInteger(), nullable=False),
        sa.Column("id_cliente", sa.BigInteger(), nullable=False),
        sa.Column("client_sync_id", sa.String(length=100), nullable=False),
        sa.Column("id_incidente", sa.BigInteger(), nullable=True),
        sa.Column("estado_sync", sa.String(length=30), nullable=False, server_default="PENDIENTE"),
        sa.Column("intentos", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("error_mensaje", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["id_tenant"], ["tenants.id_tenant"], name="fk_offline_sync_tenant"),
        sa.ForeignKeyConstraint(["id_cliente"], ["clientes.id_cliente"], name="fk_offline_sync_cliente", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["id_incidente"], ["incidentes.id_incidente"], name="fk_offline_sync_incidente", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id_sync"),
        sa.UniqueConstraint("id_tenant", "id_cliente", "client_sync_id", name="uq_offline_sync_tenant_cliente_client"),
    )
    op.create_index("ix_offline_sync_tenant_cliente", "emergencias_offline_sync", ["id_tenant", "id_cliente"])
    op.create_index("ix_offline_sync_incidente", "emergencias_offline_sync", ["id_incidente"])


def downgrade() -> None:
    existing = _tables()
    if "emergencias_offline_sync" not in existing:
        return

    op.drop_index("ix_offline_sync_incidente", table_name="emergencias_offline_sync")
    op.drop_index("ix_offline_sync_tenant_cliente", table_name="emergencias_offline_sync")
    op.drop_table("emergencias_offline_sync")
