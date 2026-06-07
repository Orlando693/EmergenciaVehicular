"""add super_admins table

Revision ID: d1e2f3a4b5c6
Revises: b7c8d9e0f1a2
Create Date: 2026-06-06

"""
from alembic import op
import sqlalchemy as sa

revision = "d1e2f3a4b5c6"
down_revision = "b7c8d9e0f1a2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "super_admins",
        sa.Column("id_superadmin", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("email",         sa.String(150),  nullable=False),
        sa.Column("password_hash", sa.String(255),  nullable=False),
        sa.Column("nombre",        sa.String(100),  nullable=False, server_default="SuperAdmin"),
        sa.Column("activo",        sa.Boolean(),    nullable=False, server_default="true"),
        sa.Column("created_at",    sa.DateTime(),   nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at",    sa.DateTime(),   nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id_superadmin"),
        sa.UniqueConstraint("email", name="uq_super_admins_email"),
    )


def downgrade() -> None:
    op.drop_table("super_admins")
