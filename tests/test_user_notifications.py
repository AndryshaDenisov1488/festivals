import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from services.user_notifications import notify_new_user


def user():
    return SimpleNamespace(user_id=123, first_name="Анна", last_name="Маркова", function="Судья <ОВД>", category="1 & 2")


def test_notice_has_identity_and_escapes_profile():
    bot = SimpleNamespace(send_message=AsyncMock())
    asyncio.run(notify_new_user(bot, -100123, user(), "anna"))
    args, kwargs = bot.send_message.call_args
    assert args[0] == -100123
    assert "Анна Маркова" in args[1]
    assert "Судья &lt;ОВД&gt;" in args[1]
    assert "1 &amp; 2" in args[1]
    assert "tg://user?id=123" in args[1] and "@anna" in args[1]
    assert kwargs["parse_mode"] == "HTML"


def test_missing_username_and_channel():
    bot = SimpleNamespace(send_message=AsyncMock())
    asyncio.run(notify_new_user(bot, "", user()))
    bot.send_message.assert_not_called()
    asyncio.run(notify_new_user(bot, -100123, user()))
    assert "Telegram:" not in bot.send_message.call_args.args[1]


def test_telegram_failure_does_not_fail_registration():
    bot = SimpleNamespace(send_message=AsyncMock(side_effect=TimeoutError()))
    asyncio.run(notify_new_user(bot, -100123, user()))
