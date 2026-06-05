"""add planes y tenant_suscripciones

Revision ID: f10a2b3c4d5e
Revises: e31f9a0b7c25
Create Date: 2026-06-04
"""
from alembic import op
import sqlalchemy as sa

revision = "f10a2b3c4d5e"
down_revision = "e31f9a0b7c25"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "planes",
        sa.Column("id_plan", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(60), nullable=False),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("precio", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("moneda", sa.String(10), nullable=False, server_default="BOB"),
        sa.Column("max_incidentes_mes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_tecnicos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_usuarios", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tiene_ia", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("tiene_reportes_avanzados", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("tiene_soporte_prioritario", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("tiene_notificaciones_push", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estado", sa.String(20), nullable=False, server_default="ACTIVO"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id_plan"),
        sa.UniqueConstraint("slug", name="uq_planes_slug"),
    )

    op.create_table(
        "tenant_suscripciones",
        sa.Column("id_suscripcion", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("id_tenant", sa.BigInteger(), nullable=False),
        sa.Column("id_plan", sa.BigInteger(), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="ACTIVO"),
        sa.Column("es_trial", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("fecha_inicio", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("fecha_fin", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["id_tenant"], ["tenants.id_tenant"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["id_plan"], ["planes.id_plan"]),
        sa.PrimaryKeyConstraint("id_suscripcion"),
        sa.UniqueConstraint("id_tenant", "estado", name="uq_tenant_suscripcion_activa"),
    )


def downgrade() -> None:
    op.drop_table("tenant_suscripciones")
    op.drop_table("planes")
