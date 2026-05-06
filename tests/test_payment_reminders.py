import os
import sys
import types
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace

os.environ.setdefault("BOT_TOKEN", "test-token")
os.environ.setdefault("ADMIN_IDS", "1")
os.environ.setdefault("CHANNEL_ID", "-1001")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


def install_payment_system_import_stubs():
    sqlalchemy = types.ModuleType("sqlalchemy")
    sqlalchemy.and_ = lambda *args: ("and", args)
    sqlalchemy.func = SimpleNamespace()

    sqlalchemy_orm = types.ModuleType("sqlalchemy.orm")
    sqlalchemy_orm.Session = object

    sqlalchemy_exc = types.ModuleType("sqlalchemy.exc")
    sqlalchemy_exc.DatabaseError = Exception

    models = types.ModuleType("models")
    models.JudgePayment = object
    models.User = object
    models.Tournament = object
    models.Registration = object
    models.RegistrationStatus = SimpleNamespace(APPROVED="approved")

    database = types.ModuleType("database")
    database.SessionLocal = lambda: None

    action_logger = types.ModuleType("utils.action_logger")
    action_logger.get_action_logger = lambda: None
    action_logger.ActionType = SimpleNamespace(
        ADMIN_CREATE_PAYMENT_RECORDS="admin_create_payment_records",
        USER_CONFIRM_PAYMENT="user_confirm_payment",
        USER_REPORT_UNPAID="user_report_unpaid",
    )

    sys.modules["sqlalchemy"] = sqlalchemy
    sys.modules["sqlalchemy.orm"] = sqlalchemy_orm
    sys.modules["sqlalchemy.exc"] = sqlalchemy_exc
    sys.modules["models"] = models
    sys.modules["database"] = database
    sys.modules["utils.action_logger"] = action_logger


install_payment_system_import_stubs()

from services.payment_system import (  # noqa: E402
    PAYMENT_REMINDER_ACTION_IGNORED,
    PAYMENT_REMINDER_ACTION_QUESTION,
    PaymentSystem,
)


class PaymentReminderDecisionTest(unittest.TestCase):
    def setUp(self):
        self.payment_system = PaymentSystem(bot=None)
        self.msk_tz = self.payment_system._msk_timezone()
        self.tournament_date = datetime(2026, 5, 6).date()

    def msk(self, year, month, day, hour, minute=0):
        return self.msk_tz.localize(datetime(year, month, day, hour, minute))

    def payment(
        self,
        *,
        reminder_sent=False,
        reminder_date=None,
        is_paid=False,
        last_payment_response_date=None,
        last_ignore_reminder_date=None,
    ):
        return SimpleNamespace(
            tournament=SimpleNamespace(date=self.tournament_date),
            is_paid=is_paid,
            reminder_sent=reminder_sent,
            reminder_date=reminder_date,
            last_payment_response_date=last_payment_response_date,
            last_ignore_reminder_date=last_ignore_reminder_date,
        )

    def test_judge_reminder_waits_until_18_msk_on_tournament_day(self):
        should_send, _, _ = self.payment_system._should_send_judge_payment_reminder(
            self.payment(),
            self.msk(2026, 5, 6, 17, 59),
        )

        self.assertFalse(should_send)

    def test_judge_first_reminder_is_due_from_18_msk(self):
        should_send, _, action = self.payment_system._should_send_judge_payment_reminder(
            self.payment(),
            self.msk(2026, 5, 6, 18),
        )

        self.assertTrue(should_send)
        self.assertEqual(PAYMENT_REMINDER_ACTION_QUESTION, action)

    def test_judge_ignore_followup_is_due_after_thirty_minutes_without_answer(self):
        first_sent_at_utc = datetime(2026, 5, 6, 15, tzinfo=timezone.utc)

        too_early, _, _ = self.payment_system._should_send_judge_payment_reminder(
            self.payment(reminder_sent=True, reminder_date=first_sent_at_utc),
            self.msk(2026, 5, 6, 18, 29),
        )
        should_send, _, action = self.payment_system._should_send_judge_payment_reminder(
            self.payment(reminder_sent=True, reminder_date=first_sent_at_utc),
            self.msk(2026, 5, 6, 18, 30),
        )

        self.assertFalse(too_early)
        self.assertTrue(should_send)
        self.assertEqual(PAYMENT_REMINDER_ACTION_IGNORED, action)

    def test_judge_six_hour_check_continues_after_unpaid_answer(self):
        unpaid_answer_at_utc = datetime(2026, 5, 6, 15, 5, tzinfo=timezone.utc)

        should_send, _, action = self.payment_system._should_send_judge_payment_reminder(
            self.payment(
                reminder_sent=True,
                reminder_date=unpaid_answer_at_utc,
                last_payment_response_date=unpaid_answer_at_utc,
            ),
            self.msk(2026, 5, 7, 0, 5),
        )

        self.assertTrue(should_send)
        self.assertEqual(PAYMENT_REMINDER_ACTION_QUESTION, action)

    def test_judge_six_hour_check_waits_after_unpaid_answer(self):
        unpaid_answer_at_utc = datetime(2026, 5, 6, 15, 5, tzinfo=timezone.utc)

        should_send, _, _ = self.payment_system._should_send_judge_payment_reminder(
            self.payment(
                reminder_sent=True,
                reminder_date=unpaid_answer_at_utc,
                last_payment_response_date=unpaid_answer_at_utc,
            ),
            self.msk(2026, 5, 6, 23),
        )

        self.assertFalse(should_send)

    def test_judge_reminders_stop_after_paid_confirmation(self):
        should_send, _, _ = self.payment_system._should_send_judge_payment_reminder(
            self.payment(is_paid=True),
            self.msk(2026, 5, 8, 0),
        )

        self.assertFalse(should_send)


if __name__ == "__main__":
    unittest.main()
