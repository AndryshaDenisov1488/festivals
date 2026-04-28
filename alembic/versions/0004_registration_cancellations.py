"""add registration_cancellations table

Revision ID: 0004_registration_cancellations
Revises: 0003_is_blocked
Create Date: 2026-04-28

"""

from alembic import op
import sqlalchemy as sa


revision = "0004_registration_cancellations"
down_revision = "0003_is_blocked"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "registration_cancellations",
        sa.Column("cancellation_id", sa.Integer(), nullable=False),
        sa.Column("registration_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tournament_id", sa.Integer(), nullable=False),
        sa.Column("previous_status", sa.String(), nullable=False),
        sa.Column("cancelled_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.tournament_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("cancellation_id"),
    )
    op.create_index("ix_registration_cancellations_cancellation_id", "registration_cancellations", ["cancellation_id"], unique=False)
    op.create_index("idx_cancellation_user", "registration_cancellations", ["user_id"], unique=False)
    op.create_index("idx_cancellation_tournament", "registration_cancellations", ["tournament_id"], unique=False)
    op.create_index("idx_cancellation_previous_status", "registration_cancellations", ["previous_status"], unique=False)
    op.create_index("idx_cancellation_cancelled_at", "registration_cancellations", ["cancelled_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_cancellation_cancelled_at", table_name="registration_cancellations")
    op.drop_index("idx_cancellation_previous_status", table_name="registration_cancellations")
    op.drop_index("idx_cancellation_tournament", table_name="registration_cancellations")
    op.drop_index("idx_cancellation_user", table_name="registration_cancellations")
    op.drop_index("ix_registration_cancellations_cancellation_id", table_name="registration_cancellations")
    op.drop_table("registration_cancellations")
