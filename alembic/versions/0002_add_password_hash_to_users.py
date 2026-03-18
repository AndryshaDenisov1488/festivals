"""add password_hash to users

Revision ID: 0002_password_hash
Revises: 0001_add_email_and_flags
Create Date: 2026-03-18

"""

from alembic import op
import sqlalchemy as sa


revision = "0002_password_hash"
down_revision = "0001_add_email_and_flags"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("password_hash", sa.String(length=255), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("password_hash")
