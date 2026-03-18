import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import joinedload
from sqlalchemy import func, and_
from database import SessionLocal
from models import User, Tournament, Registration, RegistrationStatus, JudgePayment
from config import ADMIN_IDS, MAX_JUDGES_PER_TOURNAMENT, BOT_TOKEN
from api.dependencies import get_current_admin
from api.utils import format_date, filter_by_search
from utils.date_utils import get_today


router = APIRouter()
logger = logging.getLogger(__name__)


class BroadcastIn(BaseModel):
    message: str


class AdminUserUpdateIn(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    function: Optional[str] = None
    category: Optional[str] = None
    is_blocked: Optional[bool] = None


class TournamentCreateIn(BaseModel):
    name: str
    date: str
    month: str


class TournamentUpdateIn(BaseModel):
    name: Optional[str] = None
    date: Optional[str] = None
    month: Optional[str] = None


@router.post("/broadcast")
async def broadcast(
    payload: BroadcastIn,
    admin: User = Depends(get_current_admin),
):
    from config import BOT_TOKEN
    if not BOT_TOKEN or not payload.message:
        raise HTTPException(status_code=400, detail="Invalid request")
    from aiogram import Bot
    bot = Bot(token=BOT_TOKEN)
    db = SessionLocal()
    try:
        users = db.query(User).all()
        ok, fail = 0, 0
        for u in users:
            try:
                await bot.send_message(u.user_id, payload.message, parse_mode="HTML")
                ok += 1
            except Exception:
                fail += 1
        return {"total": len(users), "ok": ok, "fail": fail}
    finally:
        db.close()
        await bot.session.close()


@router.get("/registrations")
def admin_list_registrations(
    month: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    future_only: bool = Query(True, description="Только будущие турниры"),
    search: Optional[str] = Query(None, description="Поиск по имени судьи или турниру"),
    admin: User = Depends(get_current_admin),
):
    from datetime import date

    db = SessionLocal()
    try:
        q = db.query(Registration).join(Tournament).join(User, Registration.user_id == User.user_id)
        if month:
            q = q.filter(Tournament.month == month)
        if future_only:
            from utils.date_utils import get_today
            q = q.filter(Tournament.date >= get_today())
        if status:
            q = q.filter(Registration.status == status)
        q = q.order_by(Tournament.date.asc(), Registration.registration_id)
        regs = q.all()
        if search and search.strip():
            regs = [
                r for r in regs
                if filter_by_search(
                    [r],
                    search,
                    lambda x: x.user.first_name,
                    lambda x: x.user.last_name,
                    lambda x: x.user.function,
                    lambda x: x.user.category,
                    lambda x: x.tournament.name,
                    lambda x: x.tournament.month,
                )
            ]
        return [
            {
                "registration_id": r.registration_id,
                "tournament_id": r.tournament_id,
                "tournament_name": r.tournament.name,
                "tournament_date": format_date(r.tournament.date),
                "tournament_month": r.tournament.month,
                "user_id": r.user_id,
                "user_name": f"{r.user.first_name} {r.user.last_name}",
                "status": r.status,
            }
            for r in regs
        ]
    finally:
        db.close()


async def _notify_judge_approve(user_id: int, tournament_name: str, tournament_date: str) -> None:
    """Telegram при одобрении заявки."""
    if not BOT_TOKEN:
        logger.warning("BOT_TOKEN не задан, Telegram-уведомление судье пропущено")
        return
    try:
        from aiogram import Bot
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(
            user_id,
            f"✅ Вы утверждены для судейства турнира <b>{tournament_date} {tournament_name}</b>!",
            parse_mode="HTML"
        )
        await bot.session.close()
        logger.info("Telegram approve отправлен user_id=%s", user_id)
    except Exception as e:
        logger.exception("Ошибка Telegram approve user_id=%s: %s", user_id, e)


async def _notify_judge_reject(user_id: int, tournament_name: str, tournament_date: str) -> None:
    """Telegram при отклонении заявки."""
    if not BOT_TOKEN:
        logger.warning("BOT_TOKEN не задан, Telegram-уведомление судье пропущено")
        return
    try:
        from aiogram import Bot
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(
            user_id,
            f"❌ Ваша заявка на судейство турнира <b>{tournament_date} {tournament_name}</b> отклонена.",
            parse_mode="HTML"
        )
        await bot.session.close()
        logger.info("Telegram reject отправлен user_id=%s", user_id)
    except Exception as e:
        logger.exception("Ошибка Telegram reject user_id=%s: %s", user_id, e)


@router.post("/registrations/{registration_id}/approve")
async def admin_approve_registration(
    registration_id: int,
    admin: User = Depends(get_current_admin),
):
    db = SessionLocal()
    try:
        reg = db.query(Registration).options(
            joinedload(Registration.user),
            joinedload(Registration.tournament),
        ).filter(Registration.registration_id == registration_id).first()
        if not reg:
            raise HTTPException(status_code=404, detail="Registration not found")
        if reg.status != RegistrationStatus.PENDING:
            raise HTTPException(status_code=400, detail="Registration already processed")
        approved_count = db.query(Registration).filter(
            Registration.tournament_id == reg.tournament_id,
            Registration.status == RegistrationStatus.APPROVED,
        ).count()
        if approved_count >= MAX_JUDGES_PER_TOURNAMENT:
            raise HTTPException(status_code=400, detail="Max judges reached")
        reg.status = RegistrationStatus.APPROVED
        db.commit()

        t = reg.tournament
        u = reg.user
        tournament_date = format_date(t.date)
        tournament_name = t.name

        existing = db.query(JudgePayment).filter(
            JudgePayment.user_id == u.user_id,
            JudgePayment.tournament_id == t.tournament_id,
        ).first()
        if not existing:
            db.add(JudgePayment(
                user_id=u.user_id,
                tournament_id=t.tournament_id,
                is_paid=False,
                reminder_sent=False,
            ))
            db.commit()

        await _notify_judge_approve(u.user_id, tournament_name, tournament_date)
        if u.email:
            from api.email_service import send_registration_approved_email
            try:
                send_registration_approved_email(u.email, tournament_name, tournament_date)
                logger.info("Email approve отправлен на %s", u.email)
            except Exception as e:
                logger.exception("Ошибка email approve: %s", e)
        else:
            logger.info("Email approve пропущен: у судьи user_id=%s нет email", u.user_id)

        return {"ok": True, "status": "approved"}
    finally:
        db.close()


@router.post("/registrations/{registration_id}/reject")
async def admin_reject_registration(
    registration_id: int,
    admin: User = Depends(get_current_admin),
):
    db = SessionLocal()
    try:
        reg = db.query(Registration).options(
            joinedload(Registration.user),
            joinedload(Registration.tournament),
        ).filter(Registration.registration_id == registration_id).first()
        if not reg:
            raise HTTPException(status_code=404, detail="Registration not found")
        if reg.status != RegistrationStatus.PENDING:
            raise HTTPException(status_code=400, detail="Registration already processed")
        reg.status = RegistrationStatus.REJECTED
        db.commit()

        t = reg.tournament
        u = reg.user
        tournament_date = format_date(t.date)
        tournament_name = t.name

        await _notify_judge_reject(u.user_id, tournament_name, tournament_date)
        if u.email:
            from api.email_service import send_registration_rejected_email
            try:
                send_registration_rejected_email(u.email, tournament_name, tournament_date)
                logger.info("Email reject отправлен на %s", u.email)
            except Exception as e:
                logger.exception("Ошибка email reject: %s", e)
        else:
            logger.info("Email reject пропущен: у судьи user_id=%s нет email", u.user_id)

        return {"ok": True, "status": "rejected"}
    finally:
        db.close()


# ========== Пользователи ==========
@router.get("/users")
def admin_list_users(
    search: Optional[str] = Query(None),
    admin: User = Depends(get_current_admin),
):
    db = SessionLocal()
    try:
        users = db.query(User).order_by(User.last_name, User.first_name).all()
        if search and search.strip():
            users = filter_by_search(
                users,
                search,
                lambda u: u.first_name,
                lambda u: u.last_name,
                lambda u: u.function,
                lambda u: u.category,
                lambda u: getattr(u, "email", None) or "",
            )
        return [
            {
                "user_id": u.user_id,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "function": u.function,
                "category": u.category,
                "email": getattr(u, "email", None),
                "is_blocked": getattr(u, "is_blocked", False),
            }
            for u in users
        ]
    finally:
        db.close()


@router.patch("/users/{user_id}", status_code=204)
def admin_update_user(
    user_id: int,
    payload: AdminUserUpdateIn,
    admin: User = Depends(get_current_admin),
):
    if user_id in ADMIN_IDS:
        raise HTTPException(status_code=400, detail="Нельзя редактировать админа")
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.user_id == user_id).first()
        if not u:
            raise HTTPException(status_code=404, detail="User not found")
        if payload.first_name is not None:
            u.first_name = payload.first_name.strip()
        if payload.last_name is not None:
            u.last_name = payload.last_name.strip()
        if payload.function is not None:
            u.function = payload.function.strip()
        if payload.category is not None:
            u.category = payload.category.strip()
        if payload.is_blocked is not None:
            u.is_blocked = payload.is_blocked
        db.commit()
        return
    finally:
        db.close()


# ========== Турниры ==========
@router.get("/tournaments")
def admin_list_tournaments(
    month: Optional[str] = Query(None),
    future_only: bool = Query(False),
    search: Optional[str] = Query(None),
    admin: User = Depends(get_current_admin),
):
    db = SessionLocal()
    try:
        q = db.query(Tournament)
        if month:
            q = q.filter(Tournament.month == month)
        if future_only:
            q = q.filter(Tournament.date >= get_today())
        q = q.order_by(Tournament.date)
        tours = q.all()
        if search and search.strip():
            tours = filter_by_search(tours, search, lambda t: t.name, lambda t: t.month)
        return [
            {
                "tournament_id": t.tournament_id,
                "name": t.name,
                "date": format_date(t.date),
                "month": t.month,
            }
            for t in tours
        ]
    finally:
        db.close()


MONTH_NAMES_RU = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]


def _month_from_date(d: date) -> str:
    """Месяц из даты (1–12 -> русское название)."""
    return MONTH_NAMES_RU[d.month - 1]


@router.post("/tournaments", status_code=201)
async def admin_create_tournament(
    payload: TournamentCreateIn,
    admin: User = Depends(get_current_admin),
):
    from datetime import datetime
    try:
        d = datetime.strptime(payload.date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат даты (YYYY-MM-DD)")
    month = _month_from_date(d)
    db = SessionLocal()
    try:
        t = Tournament(name=payload.name.strip(), date=d, month=month)
        db.add(t)
        db.commit()
        db.refresh(t)
        from services.payment_system import PaymentSystem
        ps = PaymentSystem(bot=None)
        await ps.create_payment_records(t.tournament_id)
        formatted = f"{format_date(t.date)} {t.name}"
        users = [u for u in db.query(User).all() if not getattr(u, "is_blocked", False)]
        if BOT_TOKEN:
            try:
                from aiogram import Bot
                import asyncio
                bot = Bot(token=BOT_TOKEN)
                for u in users:
                    try:
                        await bot.send_message(u.user_id, f"🆕 Добавлен турнир <b>{formatted}</b> в <b>{t.month}</b>.", parse_mode="HTML")
                        await asyncio.sleep(0.05)
                    except Exception:
                        pass
            except Exception as e:
                logger.exception("Notify new tournament: %s", e)
        for u in users:
            if u.email:
                try:
                    from api.email_service import send_tournament_added_email
                    send_tournament_added_email(u.email, t.name, format_date(t.date), t.month)
                except Exception as e:
                    logger.exception("Email new tournament to %s: %s", u.email, e)
        return {
            "tournament_id": t.tournament_id,
            "name": t.name,
            "date": format_date(t.date),
            "month": t.month,
        }
    finally:
        db.close()


async def _notify_tournament_change(
    old_name: str,
    old_date: date,
    old_month: str,
    new_name: str,
    new_date: date,
    new_month: str,
) -> None:
    """Отправляет уведомление об изменении турнира всем пользователям (бот + email)."""
    changes_html = []
    changes_plain = []
    if old_date != new_date:
        s = f"{old_date.strftime('%d.%m.%Y')} → {new_date.strftime('%d.%m.%Y')}"
        changes_html.append(f"📅 <b>Дата:</b> {s}")
        changes_plain.append(f"Дата: {s}")
    if old_name != new_name:
        changes_html.append(f"🏆 <b>Название:</b> {old_name} → {new_name}")
        changes_plain.append(f"Название: {old_name} → {new_name}")
    if old_month != new_month:
        changes_html.append(f"📆 <b>Месяц:</b> {old_month} → {new_month}")
        changes_plain.append(f"Месяц: {old_month} → {new_month}")
    if not changes_html:
        return
    import asyncio
    db = SessionLocal()
    try:
        users = [u for u in db.query(User).all() if not getattr(u, "is_blocked", False)]
        if BOT_TOKEN:
            from aiogram import Bot
            bot = Bot(token=BOT_TOKEN)
            message = (
                "🔄 <b>Турнир изменён</b>\n\n"
                f"🏆 <b>Турнир:</b> {new_date.strftime('%d.%m.%Y')} {new_name}\n\n"
                "📝 <b>Изменения:</b>\n" + "\n".join(f"• {c}" for c in changes_html)
            )
            for u in users:
                try:
                    await bot.send_message(u.user_id, message, parse_mode="HTML")
                    await asyncio.sleep(0.05)
                except Exception:
                    pass
        for u in users:
            if u.email:
                try:
                    from api.email_service import send_tournament_changed_email
                    send_tournament_changed_email(u.email, new_name, new_date.strftime('%d.%m.%Y'), changes_plain)
                except Exception as e:
                    logger.exception("Email tournament change to %s: %s", u.email, e)
    except Exception as e:
        logger.exception("Notify tournament change: %s", e)
    finally:
        db.close()


@router.patch("/tournaments/{tournament_id}", status_code=204)
async def admin_update_tournament(
    tournament_id: int,
    payload: TournamentUpdateIn,
    admin: User = Depends(get_current_admin),
):
    db = SessionLocal()
    try:
        t = db.query(Tournament).filter(Tournament.tournament_id == tournament_id).first()
        if not t:
            raise HTTPException(status_code=404, detail="Tournament not found")
        old_name, old_date, old_month = t.name, t.date, t.month
        if payload.name is not None:
            t.name = payload.name.strip()
        if payload.date is not None:
            from datetime import datetime
            try:
                t.date = datetime.strptime(payload.date, "%Y-%m-%d").date()
                t.month = _month_from_date(t.date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Неверный формат даты (YYYY-MM-DD)")
        elif payload.month is not None:
            t.month = payload.month.strip()
        db.commit()
        db.refresh(t)
        await _notify_tournament_change(old_name, old_date, old_month, t.name, t.date, t.month)
        return
    finally:
        db.close()


@router.get("/earnings")
def admin_earnings_list(
    future_only: bool = Query(False, description="Только будущие турниры"),
    search: Optional[str] = Query(None),
    admin: User = Depends(get_current_admin),
):
    """Список судей с заработком: турниры, указано/не указано, сумма."""
    db = SessionLocal()
    try:
        q = (
            db.query(User, JudgePayment, Tournament)
            .join(JudgePayment, JudgePayment.user_id == User.user_id)
            .join(Tournament, JudgePayment.tournament_id == Tournament.tournament_id)
            .join(
                Registration,
                and_(
                    Registration.user_id == JudgePayment.user_id,
                    Registration.tournament_id == JudgePayment.tournament_id,
                    Registration.status == RegistrationStatus.APPROVED,
                ),
            )
        )
        if future_only:
            q = q.filter(Tournament.date >= get_today())
        rows = q.order_by(User.last_name, Tournament.date.desc()).all()
        if search and search.strip():
            term = search.strip().lower()
            rows = [
                r for r in rows
                if term in (r[0].first_name or "").lower()
                or term in (r[0].last_name or "").lower()
                or term in (r[2].name or "").lower()
            ]
        by_user: dict[int, dict] = {}
        for user, payment, tournament in rows:
            if user.user_id not in by_user:
                by_user[user.user_id] = {
                    "user_id": user.user_id,
                    "user_name": f"{user.first_name} {user.last_name}",
                    "email": user.email or "",
                    "function": user.function or "",
                    "category": user.category or "",
                    "total_tournaments": 0,
                    "with_amount": 0,
                    "without_amount": 0,
                    "total_amount": 0.0,
                    "tournaments": [],
                    "without_amount_list": [],
                }
            d = by_user[user.user_id]
            d["total_tournaments"] += 1
            t_info = {
                "payment_id": payment.payment_id,
                "tournament_name": tournament.name,
                "tournament_date": format_date(tournament.date),
                "tournament_month": tournament.month,
                "amount": payment.amount,
                "is_paid": payment.is_paid,
            }
            d["tournaments"].append(t_info)
            if payment.amount is not None:
                d["with_amount"] += 1
                d["total_amount"] += payment.amount
            else:
                d["without_amount"] += 1
                d["without_amount_list"].append({
                    "payment_id": payment.payment_id,
                    "tournament_name": tournament.name,
                    "tournament_date": format_date(tournament.date),
                })
        result = list(by_user.values())

        def parse_date_for_sort(s: Optional[str]) -> tuple[int, int, int]:
            if not s:
                return (0, 0, 0)
            parts = s.split(".")
            if len(parts) != 3:
                return (0, 0, 0)
            try:
                return (int(parts[2]), int(parts[1]), int(parts[0]))
            except (ValueError, IndexError):
                return (0, 0, 0)

        for r in result:
            r["tournaments"].sort(key=lambda x: parse_date_for_sort(x.get("tournament_date")))

        return sorted(result, key=lambda x: (-x["total_amount"], x["user_name"]))
    finally:
        db.close()


class EarningsRequestIn(BaseModel):
    payment_ids: list[int]


class AdminPaymentAmountIn(BaseModel):
    amount: float


@router.patch("/earnings/payment/{payment_id}")
async def admin_set_payment_amount(
    payment_id: int,
    payload: AdminPaymentAmountIn,
    admin: User = Depends(get_current_admin),
):
    """Админ вводит заработок судьи за турнир."""
    if payload.amount < 0:
        raise HTTPException(status_code=400, detail="Сумма не может быть отрицательной")
    db = SessionLocal()
    try:
        payment = (
            db.query(JudgePayment)
            .filter(JudgePayment.payment_id == payment_id)
            .first()
        )
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        reg = db.query(Registration).filter(
            Registration.user_id == payment.user_id,
            Registration.tournament_id == payment.tournament_id,
            Registration.status == RegistrationStatus.APPROVED,
        ).first()
        if not reg:
            raise HTTPException(status_code=400, detail="Регистрация не утверждена или отменена")
        payment.amount = payload.amount
        db.commit()
        from services.budget_service import get_budget_service
        budget_service = get_budget_service(None)
        await budget_service.update_judges_payment(payment.tournament_id)
        return {"ok": True, "amount": payment.amount}
    finally:
        db.close()


@router.post("/earnings/request")
async def admin_earnings_request(
    payload: EarningsRequestIn,
    admin: User = Depends(get_current_admin),
):
    """Отправить судье запрос указать заработок (бот + email)."""
    if not payload.payment_ids:
        raise HTTPException(status_code=400, detail="payment_ids required")
    db = SessionLocal()
    try:
        payments = (
            db.query(JudgePayment, Tournament, User)
            .join(Tournament, JudgePayment.tournament_id == Tournament.tournament_id)
            .join(User, JudgePayment.user_id == User.user_id)
            .filter(JudgePayment.payment_id.in_(payload.payment_ids))
            .all()
        )
        if not payments:
            raise HTTPException(status_code=404, detail="Payments not found")
        by_user: dict[int, list] = {}
        for p, t, u in payments:
            if p.amount is not None:
                continue
            if u.user_id not in by_user:
                by_user[u.user_id] = []
            by_user[u.user_id].append((u, t))
        if not by_user:
            return {"sent": 0, "message": "Все суммы уже указаны"}
        import asyncio
        from aiogram import Bot
        bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None
        sent = 0
        for user_id, items in by_user.items():
            user = items[0][0]
            tournaments = [(t.name, format_date(t.date)) for _, t in items]
            if len(tournaments) == 1:
                msg = (
                    f"💰 <b>Укажите заработок</b>\n\n"
                    f"Пожалуйста, укажите ваш заработок за турнир <b>{tournaments[0][0]}</b> ({tournaments[0][1]}).\n\n"
                    "Сделайте это в боте или на веб-портале."
                )
            else:
                lines = "\n".join(f"• {n} ({d})" for n, d in tournaments)
                msg = (
                    f"💰 <b>Укажите заработок</b>\n\n"
                    f"Пожалуйста, укажите ваш заработок за турниры:\n\n{lines}\n\n"
                    "Сделайте это в боте или на веб-портале."
                )
            if bot:
                try:
                    await bot.send_message(user.user_id, msg, parse_mode="HTML")
                    sent += 1
                    await asyncio.sleep(0.05)
                except Exception as e:
                    logger.exception("Earnings request to %s: %s", user.user_id, e)
            if user.email:
                try:
                    from api.email_service import send_earnings_request_email
                    send_earnings_request_email(user.email, f"{user.first_name} {user.last_name}", tournaments)
                    sent += 1
                except Exception as e:
                    logger.exception("Earnings request email to %s: %s", user.email, e)
        return {"sent": sent}
    finally:
        db.close()


@router.delete("/tournaments/{tournament_id}", status_code=204)
async def admin_delete_tournament(
    tournament_id: int,
    admin: User = Depends(get_current_admin),
):
    db = SessionLocal()
    try:
        t = db.query(Tournament).filter(Tournament.tournament_id == tournament_id).first()
        if not t:
            raise HTTPException(status_code=404, detail="Tournament not found")
        title = f"{format_date(t.date)} {t.name}"
        month = t.month
        db.delete(t)
        db.commit()
        users = [u for u in db.query(User).all() if not getattr(u, "is_blocked", False)]
        if BOT_TOKEN:
            import asyncio
            from aiogram import Bot
            bot = Bot(token=BOT_TOKEN)
            msg = f"❗️ Турнир «{title}» ({month}) удалён админом."
            for u in users:
                try:
                    await bot.send_message(u.user_id, msg)
                    await asyncio.sleep(0.05)
                except Exception:
                    pass
        for u in users:
            if u.email:
                try:
                    from api.email_service import send_tournament_deleted_email
                    send_tournament_deleted_email(u.email, title, month)
                except Exception as e:
                    logger.exception("Email tournament deleted to %s: %s", u.email, e)
        return
    finally:
        db.close()
