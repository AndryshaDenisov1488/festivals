import os
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace

os.environ.setdefault("BOT_TOKEN", "test-token")
os.environ.setdefault("ADMIN_IDS", "1")
os.environ.setdefault("CHANNEL_ID", "-1001")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from services.payment_system import PaymentSystem  # noqa: E402


class PaymentReminderDecisionTest(unittest.TestCase):
    def setUp(self):
        self.payment_system = PaymentSystem(bot=None)
        self.msk_tz = self.payment_system._msk_timezone()
        self.tournament_date = datetime(2026, 5, 6).date()

    def msk(self, year, month, day, hour, minute=0):
        return self.msk_tz.localize(datetime(year, month, day, hour, minute))

    def payment(self, *, reminder_sent=False, reminder_date=None):
        return SimpleNamespace(
            tournament=SimpleNamespace(date=self.tournament_date),
            reminder_sent=reminder_sent,
            reminder_date=reminder_date,
        )

    def test_judge_reminder_waits_until_18_msk_on_tournament_day(self):
        should_send, _ = self.payment_system._should_send_judge_payment_reminder(
            self.payment(),
            self.msk(2026, 5, 6, 17, 59),
        )

        self.assertFalse(should_send)

    def test_judge_first_reminder_is_due_from_18_msk(self):
        should_send, _ = self.payment_system._should_send_judge_payment_reminder(
            self.payment(),
            self.msk(2026, 5, 6, 18),
        )

        self.assertTrue(should_send)

    def test_judge_repeat_reminder_is_due_after_six_hours(self):
        first_sent_at_utc = datetime(2026, 5, 6, 15, tzinfo=timezone.utc)

        should_send, _ = self.payment_system._should_send_judge_payment_reminder(
            self.payment(reminder_sent=True, reminder_date=first_sent_at_utc),
            self.msk(2026, 5, 7, 0),
        )

        self.assertTrue(should_send)

    def test_judge_reminders_stop_after_negative_answer_marker(self):
        stop_marker_utc = datetime(2027, 5, 6, 15, tzinfo=timezone.utc)

        should_send, _ = self.payment_system._should_send_judge_payment_reminder(
            self.payment(reminder_sent=True, reminder_date=stop_marker_utc),
            self.msk(2026, 5, 7, 0),
        )

        self.assertFalse(should_send)

    def test_judge_reminders_stop_after_planned_attempt_limit(self):
        should_send, _ = self.payment_system._should_send_judge_payment_reminder(
            self.payment(),
            self.msk(2026, 5, 8, 0),
        )

        self.assertFalse(should_send)

    def test_admin_reminder_uses_same_schedule_window(self):
        before_first, _ = self.payment_system._should_include_in_admin_payment_reminder(
            self.payment(),
            self.msk(2026, 5, 6, 17, 59),
        )
        first_due, _ = self.payment_system._should_include_in_admin_payment_reminder(
            self.payment(),
            self.msk(2026, 5, 6, 18),
        )
        repeat_due, _ = self.payment_system._should_include_in_admin_payment_reminder(
            self.payment(),
            self.msk(2026, 5, 7, 0),
        )
        after_limit, _ = self.payment_system._should_include_in_admin_payment_reminder(
            self.payment(),
            self.msk(2026, 5, 8, 0),
        )

        self.assertFalse(before_first)
        self.assertTrue(first_due)
        self.assertTrue(repeat_due)
        self.assertFalse(after_limit)


if __name__ == "__main__":
    unittest.main()
