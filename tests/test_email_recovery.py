import importlib
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def auth_db(monkeypatch, tmp_path):
    monkeypatch.setenv("BOT_TOKEN", "12345:unused-test-token")
    monkeypatch.setenv("ADMIN_IDS", "123")
    monkeypatch.setenv("CHANNEL_ID", "123")
    auth = importlib.import_module("api.routers.auth")
    from models import Base, User
    engine = create_engine("sqlite:///" + str(tmp_path / "auth.db"))
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(auth, "SessionLocal", factory)
    with factory() as db:
        db.add(User(user_id=123, first_name="Имя", last_name="Фамилия", function="Судья", category="1", email="judge@example.com",
                    email_verified=False, email_verification_code="long-random-token123", email_verification_expires_at=None))
        db.commit()
    yield auth, factory, User
    engine.dispose()


def test_recovery_confirms_and_consumes_once(auth_db):
    auth, factory, User = auth_db
    payload = auth.AuthVerifyCodeIn(email="judge@example.com", code="long-random-token123")
    assert auth.verify_code(payload).access_token
    with factory() as db:
        user = db.get(User, 123)
        assert user.email_verified and user.email_verification_code is None
    with pytest.raises(auth.HTTPException):
        auth.verify_code(payload)


def test_expired_or_blocked_cannot_redeem(auth_db):
    auth, factory, User = auth_db
    payload = auth.AuthVerifyCodeIn(email="judge@example.com", code="long-random-token123")
    with factory() as db:
        db.get(User, 123).email_verification_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()
    with pytest.raises(auth.HTTPException):
        auth.verify_code(payload)
    with factory() as db:
        user = db.get(User, 123)
        user.email_verification_expires_at = None
        user.is_blocked = True
        db.commit()
    with pytest.raises(auth.HTTPException):
        auth.verify_code(payload)


def test_resend_failure_restores_and_success_is_idempotent(auth_db, tmp_path):
    from maintenance.recover_email_20261106 import recover
    _, factory, User = auth_db
    receipt = tmp_path / "receipt.json"
    assert recover(factory, lambda *a: False, User, [123], receipt, "https://example.com", True)[0]["status"] == "failed"
    with factory() as db:
        assert db.get(User, 123).email_verification_code == "long-random-token123"
    messages = []
    def send(*args):
        messages.append(args)
        return True
    assert recover(factory, send, User, [123], receipt, "https://example.com", True)[0]["status"] == "sent"
    assert recover(factory, send, User, [123], receipt, "https://example.com", True)[0]["status"] == "already_sent"
    assert len(messages) == 1


def test_mail_failures_are_reported(monkeypatch):
    from api import email_service as mail
    monkeypatch.setattr(mail, "SMTP_HOST", "")
    assert mail.send_login_code_email("judge@example.com", "123456") is False
    monkeypatch.setattr(mail, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(mail, "SMTP_FROM", "sender@example.com")
    monkeypatch.setattr(mail, "SMTP_PORT", 465)
    def fail(*a, **kw):
        raise TimeoutError("test timeout")
    monkeypatch.setattr(mail.smtplib, "SMTP_SSL", fail)
    assert mail.send_login_code_email("judge@example.com", "123456") is False


def test_resend_does_not_overwrite_newer_request(auth_db, tmp_path, monkeypatch):
    from maintenance import recover_email_20261106 as recovery
    _, factory, User = auth_db
    def concurrent_request(_):
        with factory() as db:
            db.get(User, 123).email_verification_code = "newer-request-code"
            db.commit()
        return "recovery-token-123456"
    monkeypatch.setattr(recovery.secrets, "token_urlsafe", concurrent_request)
    sent = []
    result = recovery.recover(factory, lambda *args: sent.append(args), User, [123], tmp_path / "receipt.json", "https://example.com", True)
    assert result[0]["status"] == "changed_concurrently"
    assert not sent
    with factory() as db:
        assert db.get(User, 123).email_verification_code == "newer-request-code"
