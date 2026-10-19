import os
os.environ.setdefault("BOT_TOKEN", "test-token")
os.environ.setdefault("ADMIN_IDS", "1")
os.environ.setdefault("CHANNEL_ID", "-1001")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ["SPECIAL_JUDGE_IDS"] = "946719504"

import importlib
import config
importlib.reload(config)
import services.payment_rules as rules
importlib.reload(rules)

from services.payment_rules import check_payment_amount, parse_amount_message


def test_standard_amount_ok():
    assert check_payment_amount(1, 5000) == "ok"


def test_below_minimum():
    assert check_payment_amount(1, 3499) == "min"


def test_non_standard_needs_confirm():
    assert check_payment_amount(1, 4000) == "non_standard"
    assert check_payment_amount(1, 4000, confirm_non_standard=True) == "ok"


def test_special_judge_any_positive():
    assert check_payment_amount(946719504, 100) == "ok"
    assert check_payment_amount(946719504, 0) == "positive"


def test_parse_yes_confirms_pending():
    amount, confirmed, err = parse_amount_message("да", 4000)
    assert err is None
    assert confirmed is True
    assert amount == 4000
