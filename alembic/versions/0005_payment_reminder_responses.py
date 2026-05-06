"""add payment reminder response tracking

Revision ID: 0005_payment_reminder_responses
Revises: 0004_registration_cancellations
Create Date: 2026-05-06

"""

from alembic import op
import sqlalchemy as sa


revision = "0005_payment_reminder_responses"
down_revision = "0004_registration_cancellations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("judge_payments", sa.Column("last_payment_response_status", sa.String(length=20), nullable=True))
    op.add_column("judge_payments", sa.Column("last_payment_response_date", sa.DateTime(), nullable=True))
    op.add_column("judge_payments", sa.Column("last_ignore_reminder_date", sa.DateTime(), nullable=True))
    # Старый код ставил reminder_date далеко в будущее, когда судья отвечал
    # "Нет". В новой схеме это обычный ответ unpaid, после которого проверки
    # продолжаются через 6 часов.
    op.execute(
        """
        UPDATE judge_payments
        SET last_payment_response_status = 'unpaid',
            last_payment_response_date = CURRENT_TIMESTAMP,
            reminder_date = CURRENT_TIMESTAMP
        WHERE is_paid = 0
          AND reminder_date IS NOT NULL
          AND reminder_date > CURRENT_TIMESTAMP
        """
    )
    op.create_index("idx_payment_response_status", "judge_payments", ["last_payment_response_status"], unique=False)
    op.create_index("idx_payment_response_date", "judge_payments", ["last_payment_response_date"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_payment_response_date", table_name="judge_payments")
    op.drop_index("idx_payment_response_status", table_name="judge_payments")
    op.drop_column("judge_payments", "last_ignore_reminder_date")
    op.drop_column("judge_payments", "last_payment_response_date")
    op.drop_column("judge_payments", "last_payment_response_status")
