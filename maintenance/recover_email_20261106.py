"""Explicit recovery for failed email requests. Default is dry-run; no tokens logged."""
import argparse
import html
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode


def recover(session_factory, send_email, user_model, user_ids, receipt: Path, portal: str, send=False):
    history = json.loads(receipt.read_text(encoding="utf-8")) if receipt.exists() else []
    results = []
    for user_id in user_ids:
        with session_factory() as db:
            user = db.query(user_model).filter(user_model.user_id == user_id).first()
            if not user or user.is_blocked or user.email_verified or not user.email or not user.email_verification_code:
                results.append({"user_id": user_id, "status": "not_pending"})
                continue
            if any(r["user_id"] == user_id and r["email"] == user.email and r["status"] == "sent" for r in history):
                results.append({"user_id": user_id, "status": "already_sent"})
                continue
            if not send:
                results.append({"user_id": user_id, "email": user.email, "status": "would_send"})
                continue
            old_code, old_expiry = user.email_verification_code, user.email_verification_expires_at
            code = secrets.token_urlsafe(15)  # 120 bits; fits existing VARCHAR(20).
            email = user.email
            changed = db.query(user_model).filter(
                user_model.user_id == user_id,
                user_model.email == email,
                user_model.email_verified.is_(False),
                user_model.is_blocked.is_(False),
                user_model.email_verification_code == old_code,
                user_model.email_verification_expires_at == old_expiry,
            ).update({
                user_model.email_verification_code: code,
                user_model.email_verification_expires_at: None,
            }, synchronize_session=False)
            if changed != 1:
                db.rollback()
                results.append({"user_id": user_id, "status": "changed_concurrently"})
                continue
            db.commit()
            link = portal.rstrip("/") + "/api/v1/auth/recover-email#" + urlencode({"email": email, "code": code})
            text = (
                "Здравствуйте! Почта фестивальчиков снова работает.\n\n"
                "Ранее вы запрашивали код, но письмо не удалось доставить. "
                "Подтвердите почту и войдите в кабинет по ссылке:\n\n" + link + "\n\n"
                "Ссылка без срока истечения, действует один раз. "
                "Новый запрос кода заменяет эту ссылку. Откройте её и нажмите "
                "«Подтвердить почту и войти». После входа можно задать пароль в профиле.\n\n"
                "Если вы не запрашивали привязку, не переходите по ссылке."
            )
            sent = send_email(email, "Почта восстановлена — подтвердите адрес", text,
                              "<p>" + html.escape(text).replace("\n", "<br>") + "</p><p><a href=\"" + html.escape(link, quote=True) + "\">Подтвердить почту и войти</a></p>")
            if not sent:
                db.query(user_model).filter(user_model.user_id == user_id, user_model.email_verification_code == code).update({
                    user_model.email_verification_code: old_code,
                    user_model.email_verification_expires_at: old_expiry,
                }, synchronize_session=False)
                db.commit()
            result = {"user_id": user_id, "email": email, "status": "sent" if sent else "failed",
                      "at": datetime.now(timezone.utc).isoformat()}
            history.append(result)
            receipt.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
            results.append(result)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user-ids", type=int, nargs="+", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--send", action="store_true")
    args = parser.parse_args()
    # Import configuration first so dotenv is loaded before SMTP constants.
    from config import WEB_PORTAL_URL
    from database import SessionLocal
    from models import User
    from api.email_service import send_email
    print(json.dumps(recover(SessionLocal, send_email, User, args.user_ids, args.receipt, WEB_PORTAL_URL, args.send), ensure_ascii=False))
