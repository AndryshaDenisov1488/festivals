"""add is_blocked to users

Revision ID: 0003_is_blocked
Revises: 0002_password_hash
Create Date: 2026-03-18

"""

from alembic import op
import sqlalchemy as sa


revision = "0003_is_blocked"
down_revision = "0002_password_hash"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("is_blocked")
