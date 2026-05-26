"""Add multi-tenant base

Revision ID: b6f4d2a1c9e8
Revises: 49340e547c4a
Create Date: 2026-05-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b6f4d2a1c9e8"
down_revision: Union[str, None] = "49340e547c4a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TENANTED_TABLES = (
    "usuarios",
    "clientes",
    "talleres",
    "tecnicos",
    "vehiculos",
    "incidentes",
    "pagos",
    "bitacora",
    "incidente_historial",
    "mensajes_chat",
    "notificaciones",
    "dispositivos_push",
)

INDEXED_TABLES = (
    "usuarios",
    "clientes",
    "talleres",
    "tecnicos",
    "vehiculos",
    "incidentes",
    "pagos",
    "bitacora",
    "mensajes_chat",
    "notificaciones",
    "dispositivos_push",
)


def _tables() -> set[str]:
    bind = op.get_bind()
    return set(sa.inspect(bind).get_table_names())


def _columns(table_name: str) -> set[str]:
    bind = op.get_bind()
    return {col["name"] for col in sa.inspect(bind).get_columns(table_name)}


def _foreign_keys(table_name: str) -> set[str]:
    bind = op.get_bind()
    return {fk["name"] for fk in sa.inspect(bind).get_foreign_keys(table_name)}


def _indexes(table_name: str) -> set[str]:
    bind = op.get_bind()
    return {idx["name"] for idx in sa.inspect(bind).get_indexes(table_name)}


def upgrade() -> None:
    existing = _tables()

    if "tenants" not in existing:
        op.create_table(
            "tenants",
            sa.Column("id_tenant", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("nombre", sa.String(length=150), nullable=False),
            sa.Column("slug", sa.String(length=100), nullable=False),
            sa.Column("estado", sa.String(length=30), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id_tenant"),
            sa.UniqueConstraint("slug"),
        )
        op.create_index("ix_tenants_slug", "tenants", ["slug"], unique=True)

    bind = op.get_bind()
    tenant_id = bind.execute(
        sa.text(
            """
            INSERT INTO tenants (nombre, slug, estado, created_at, updated_at)
            VALUES ('Tenant Demo', 'tenant-demo', 'ACTIVO', now(), now())
            ON CONFLICT (slug) DO UPDATE
                SET nombre = EXCLUDED.nombre,
                    estado = EXCLUDED.estado,
                    updated_at = now()
            RETURNING id_tenant
            """
        )
    ).scalar_one()

    existing = _tables()
    for table_name in TENANTED_TABLES:
        if table_name not in existing:
            continue

        if "id_tenant" not in _columns(table_name):
            op.add_column(table_name, sa.Column("id_tenant", sa.BigInteger(), nullable=True))

        op.execute(
            sa.text(f"UPDATE {table_name} SET id_tenant = :tenant_id WHERE id_tenant IS NULL")
            .bindparams(tenant_id=tenant_id)
        )
        op.alter_column(table_name, "id_tenant", existing_type=sa.BigInteger(), nullable=False)
        fk_name = f"fk_{table_name}_id_tenant_tenants"
        if fk_name not in _foreign_keys(table_name):
            op.create_foreign_key(
                fk_name,
                table_name,
                "tenants",
                ["id_tenant"],
                ["id_tenant"],
            )

        if table_name in INDEXED_TABLES:
            index_name = f"ix_{table_name}_id_tenant"
            if index_name not in _indexes(table_name):
                op.create_index(index_name, table_name, ["id_tenant"])


def downgrade() -> None:
    existing = _tables()
    for table_name in reversed(TENANTED_TABLES):
        if table_name not in existing:
            continue
        if table_name in INDEXED_TABLES and f"ix_{table_name}_id_tenant" in _indexes(table_name):
            op.drop_index(f"ix_{table_name}_id_tenant", table_name=table_name)
        if f"fk_{table_name}_id_tenant_tenants" in _foreign_keys(table_name):
            op.drop_constraint(f"fk_{table_name}_id_tenant_tenants", table_name, type_="foreignkey")
        if "id_tenant" in _columns(table_name):
            op.drop_column(table_name, "id_tenant")

    if "tenants" in existing:
        if "ix_tenants_slug" in _indexes("tenants"):
            op.drop_index("ix_tenants_slug", table_name="tenants")
        op.drop_table("tenants")
