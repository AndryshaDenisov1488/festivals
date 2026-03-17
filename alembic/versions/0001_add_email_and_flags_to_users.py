"""add email and flags to users

Revision ID: 0001_add_email_and_flags
Revises: 
Create Date: 2026-03-17
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_add_email_and_flags"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQLite supports simple ADD COLUMN operations
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("email", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.text("0")))
        batch_op.add_column(sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("0")))
        batch_op.add_column(sa.Column("email_verification_code", sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column("email_verification_expires_at", sa.DateTime(), nullable=True))

    op.create_index("ix_users_email", "users", ["email"], unique=True)


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("email_verification_expires_at")
        batch_op.drop_column("email_verification_code")
        batch_op.drop_column("is_admin")
        batch_op.drop_column("email_verified")
        batch_op.drop_column("email")

    op.drop_index("ix_users_email", table_name="users")

