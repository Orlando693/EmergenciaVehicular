"""add backup_registros and backup_config

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-06-05
"""
from alembic import op
import sqlalchemy as sa

revision = "b7c8d9e0f1a2"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "backup_registros",
        sa.Column("id_backup",      sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("id_tenant",      sa.BigInteger(), sa.ForeignKey("tenants.id_tenant"), nullable=False),
        sa.Column("id_usuario",     sa.BigInteger(), sa.ForeignKey("usuarios.id_usuario", ondelete="SET NULL"), nullable=True),
        sa.Column("tipo",           sa.String(20),  nullable=False, server_default="MANUAL"),
        sa.Column("estado",         sa.String(20),  nullable=False, server_default="COMPLETADO"),
        sa.Column("nombre_archivo", sa.String(255), nullable=True),
        sa.Column("tamano_bytes",   sa.BigInteger(), server_default="0"),
        sa.Column("datos_json",     sa.Text(),       nullable=True),
        sa.Column("created_at",     sa.DateTime(),   nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_backup_registros_tenant", "backup_registros", ["id_tenant"])

    op.create_table(
        "backup_config",
        sa.Column("id_config",       sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("id_tenant",       sa.BigInteger(), sa.ForeignKey("tenants.id_tenant"), nullable=False, unique=True),
        sa.Column("activo",          sa.Boolean(),   nullable=False, server_default="false"),
        sa.Column("frecuencia",      sa.String(20),  server_default="DIARIO"),
        sa.Column("hora",            sa.String(5),   server_default="02:00"),
        sa.Column("proximo_backup",  sa.DateTime(),  nullable=True),
        sa.Column("ultimo_backup",   sa.DateTime(),  nullable=True),
        sa.Column("updated_at",      sa.DateTime(),  nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("backup_config")
    op.drop_index("ix_backup_registros_tenant", table_name="backup_registros")
    op.drop_table("backup_registros")
