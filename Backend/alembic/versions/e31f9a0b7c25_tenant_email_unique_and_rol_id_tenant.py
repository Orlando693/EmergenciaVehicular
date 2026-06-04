"""tenant: email unico por tenant y id_tenant en roles

Revision ID: e31f9a0b7c25
Revises: d20b8f1a6c33
Create Date: 2026-06-03

Cambios:
  1. usuarios: reemplaza unique(email) por unique(id_tenant, email)
  2. roles: agrega columna id_tenant nullable + índice
"""
from alembic import op
import sqlalchemy as sa


revision = 'e31f9a0b7c25'
down_revision = 'd20b8f1a6c33'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. usuarios: cambiar unique(email) → unique(id_tenant, email) ──────────
    # Eliminar constraint único existente en email
    op.drop_constraint('usuarios_email_key', 'usuarios', type_='unique')

    # Crear constraint compuesto por tenant + email
    op.create_unique_constraint(
        'uq_usuarios_tenant_email',
        'usuarios',
        ['id_tenant', 'email'],
    )

    # ── 2. roles: agregar columna id_tenant nullable ──────────────────────────
    op.add_column(
        'roles',
        sa.Column(
            'id_tenant',
            sa.BigInteger(),
            sa.ForeignKey('tenants.id_tenant', ondelete='CASCADE'),
            nullable=True,
        ),
    )
    op.create_index('ix_roles_id_tenant', 'roles', ['id_tenant'])


def downgrade() -> None:
    # Revertir roles
    op.drop_index('ix_roles_id_tenant', table_name='roles')
    op.drop_column('roles', 'id_tenant')

    # Revertir usuarios
    op.drop_constraint('uq_usuarios_tenant_email', 'usuarios', type_='unique')
    op.create_unique_constraint('usuarios_email_key', 'usuarios', ['email'])
