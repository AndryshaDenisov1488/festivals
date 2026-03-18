import logging
import asyncio
import re
from aiogram import types
from aiogram.dispatcher import FSMContext
from sqlalchemy.exc import SQLAlchemyError, DatabaseError
from sqlalchemy.orm import joinedload
from sqlalchemy import and_
import sqlite3
from database import SessionLocal
from models import User, Tournament, Registration, RegistrationStatus
from states import EditProfile, MyRegistrations, CorrectEarnings, LinkEmail
from config import CHANNEL_ID, MAX_MESSAGE_LENGTH, MAX_JUDGES_PER_TOURNAMENT, WEB_PORTAL_URL, ADMIN_EMAIL
from keyboards import main_menu
from services.excel_export import split_text
from utils.error_monitor import get_error_monitor
from utils.action_logger import get_action_logger, ActionType
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode

# Разрешаем буквы RU/EN + дефис, длина 2..30
_NAME_RE = re.compile(r"^[A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё\-]{1,29}$")
# Простая валидация email
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

logger = logging.getLogger(__name__)


# ======== Редактирование профиля ========
async def edit_profile_step(callback_query: types.CallbackQuery):
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.user_id == callback_query.from_user.id).first()
        if not user:
            await callback_query.message.answer("❌ Вы не зарегистрированы в системе.")
            await callback_query.answer()
            return
        await callback_query.message.answer(
            "📝 Вы можете изменить свои данные. Введите ваше <b>имя</b>:",
            parse_mode=ParseMode.HTML
        )
        await EditProfile.waiting_for_first_name.set()
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при загрузке профиля пользователя {callback_query.from_user.id}: {e}")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
    finally:
        session.close()
        await callback_query.answer()


async def process_edit_profile_first_name(message: types.Message, state: FSMContext):
    try:
        if not message.text:
            await message.answer("❌ Пожалуйста, отправьте текстовое сообщение.")
            return
            
        first_name = message.text.strip()
        # нормализация пробелов
        first_name = re.sub(r"\s+", " ", first_name)
        
        if not _NAME_RE.match(first_name):
            await message.answer(
                "❌ Пожалуйста, введите корректное <b>имя</b>:\n"
                "• только буквы (рус/англ) и дефис\n"
                "• длина от 2 до 30 символов\n\n"
                "Например: <code>Андрей</code> или <code>Анна-Мария</code>",
                parse_mode=ParseMode.HTML,
            )
            return
            
        await state.update_data(first_name=first_name)
        await message.answer("Введите вашу <b>фамилию</b>:", parse_mode=ParseMode.HTML)
        await EditProfile.next()
        
    except Exception as e:
        logger.error(f"Ошибка в process_edit_profile_first_name: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")
        await state.finish()


async def process_edit_profile_last_name(message: types.Message, state: FSMContext):
    try:
        if not message.text:
            await message.answer("❌ Пожалуйста, отправьте текстовое сообщение.")
            return
            
        last_name = message.text.strip()
        # нормализация пробелов
        last_name = re.sub(r"\s+", " ", last_name)
        
        if not _NAME_RE.match(last_name):
            await message.answer(
                "❌ Пожалуйста, введите корректную <b>фамилию</b>:\n"
                "• только буквы (рус/англ) и дефис\n"
                "• длина от 2 до 30 символов",
                parse_mode=ParseMode.HTML,
            )
            return
            
        await state.update_data(last_name=last_name)
        await message.answer("Введите вашу <b>судейскую функцию</b> (например, Главный судья):", parse_mode=ParseMode.HTML)
        await EditProfile.next()
        
    except Exception as e:
        logger.error(f"Ошибка в process_edit_profile_last_name: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")
        await state.finish()


async def process_edit_profile_function(message: types.Message, state: FSMContext):
    try:
        if not message.text:
            await message.answer("❌ Пожалуйста, отправьте текстовое сообщение.")
            return
            
        function = message.text.strip()
        if not function:
            await message.answer("❌ Поле не может быть пустым. Введите вашу судейскую функцию:", parse_mode=ParseMode.HTML)
            return
            
        await state.update_data(function=function)
        await message.answer("Введите вашу <b>категорию</b> (например 1 категория, 2 и тд):", parse_mode=ParseMode.HTML)
        await EditProfile.next()
        
    except Exception as e:
        logger.error(f"Ошибка в process_edit_profile_function: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")
        await state.finish()


async def process_edit_profile_category(message: types.Message, state: FSMContext):
    try:
        if not message.text:
            await message.answer("❌ Пожалуйста, отправьте текстовое сообщение.")
            return
            
        category = message.text.strip()
        if not category:
            await message.answer("❌ Поле не может быть пустым. Введите вашу категорию:", parse_mode=ParseMode.HTML)
            return
            
        data = await state.get_data()
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.user_id == message.from_user.id).first()
            if user:
                user.first_name = data['first_name']
                user.last_name = data['last_name']
                user.function = data['function']
                user.category = category
                session.commit()
                logger.info(f"Профиль пользователя {user.user_id} обновлён.")
                from utils.menu_manager import get_menu_manager
                menu_manager = get_menu_manager()
                await menu_manager.return_to_menu(
                    message, state, 
                    "✅ Ваш профиль успешно обновлён!",
                    ActionType.USER_EDIT_PROFILE
                )
            else:
                await message.answer("❌ Пользователь не найден.")
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при обновлении профиля пользователя {message.from_user.id}: {e}")
            await message.answer("❌ Произошла ошибка при обновлении профиля. Попробуйте позже.")
        finally:
            session.close()
            await state.finish()
            
    except Exception as e:
        logger.error(f"Ошибка в process_edit_profile_category: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")
        await state.finish()


# ======== Привязка email (для входа на веб-портал) ========
async def cmd_link_email(message: types.Message, state: FSMContext):
    """Команда /link_email — то же, что кнопка «Привязать email» (удобно для рассылки)"""
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.user_id == message.from_user.id).first()
        if not user:
            await message.answer("❌ Вы не зарегистрированы в системе.")
            return
        if user.email and getattr(user, "email_verified", False):
            await message.answer(
                f"✅ Email уже привязан: <code>{user.email}</code>\n\n"
                f"Вы можете входить на <a href=\"{WEB_PORTAL_URL}\">веб-портал</a> для судей.",
                parse_mode=ParseMode.HTML
            )
            return
        await message.answer(
            "📧 Введите ваш <b>email</b> для входа на веб-портал судей:\n\n"
            "Код подтверждения будет отправлен на указанный адрес.\n\n"
            "⚠️ Используете Яндекс.Почту? Проверьте папку «Спам» — письмо часто попадает туда.",
            parse_mode=ParseMode.HTML
        )
        await LinkEmail.waiting_for_email.set()
    finally:
        session.close()


async def link_email_step(callback_query: types.CallbackQuery, state: FSMContext):
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.user_id == callback_query.from_user.id).first()
        if not user:
            await callback_query.message.answer("❌ Вы не зарегистрированы в системе.")
            await callback_query.answer()
            return
        if user.email and getattr(user, "email_verified", False):
            await callback_query.message.answer(
                f"✅ Email уже привязан: <code>{user.email}</code>\n\n"
                f"Вы можете входить на <a href=\"{WEB_PORTAL_URL}\">веб-портал</a> для судей.",
                parse_mode=ParseMode.HTML
            )
            await callback_query.answer()
            return
        await callback_query.message.answer(
            "📧 Введите ваш <b>email</b> для входа на веб-портал судей:\n\n"
            "Код подтверждения будет отправлен на указанный адрес.\n\n"
            "⚠️ Используете Яндекс.Почту? Проверьте папку «Спам» — письмо часто попадает туда.",
            parse_mode=ParseMode.HTML
        )
        await LinkEmail.waiting_for_email.set()
    finally:
        session.close()
        await callback_query.answer()


async def process_link_email_input(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Введите email.")
        return
    email = message.text.strip().lower()
    if not _EMAIL_RE.match(email):
        await message.answer("❌ Некорректный email. Пример: example@gmail.com")
        return
    session = SessionLocal()
    try:
        existing = session.query(User).filter(User.email == email).first()
        if existing and existing.user_id != message.from_user.id:
            await message.answer("❌ Этот email уже привязан к другому аккаунту.")
            await state.finish()
            return
        from datetime import datetime, timedelta, timezone
        import random
        import string
        from api.email_service import send_login_code_email

        code = "".join(random.choices(string.digits, k=6))
        now = datetime.now(timezone.utc)
        user = session.query(User).filter(User.user_id == message.from_user.id).first()
        if not user:
            await message.answer("❌ Пользователь не найден.")
            await state.finish()
            return
        user.email = email
        user.email_verified = False
        user.email_verification_code = code
        user.email_verification_expires_at = now + timedelta(minutes=15)
        session.commit()

        send_login_code_email(email, code)
        await state.update_data(email=email)
        await LinkEmail.waiting_for_code.set()
        await message.answer(
            f"📧 Код отправлен на <b>{email}</b>\n\n"
            "Введите 6-значный код из письма.\n\n"
            "⚠️ Яндекс.Почта? Проверьте папку «Спам» — письмо часто попадает туда.",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Ошибка привязки email: {e}")
        await message.answer("❌ Ошибка. Проверьте настройки SMTP или попробуйте позже.")
        await state.finish()
    finally:
        session.close()


async def process_link_email_code(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Введите код из письма.")
        return
    code = message.text.strip().replace(" ", "")
    if len(code) != 6 or not code.isdigit():
        await message.answer("❌ Введите 6-значный код.")
        return
    data = await state.get_data()
    email = data.get("email", "")
    if not email:
        await message.answer("❌ Сессия истекла. Начните заново: /start")
        await state.finish()
        return
    session = SessionLocal()
    try:
        from datetime import datetime, timezone

        user = session.query(User).filter(User.user_id == message.from_user.id, User.email == email).first()
        if not user:
            await message.answer("❌ Ошибка. Начните заново: /start")
            await state.finish()
            return
        if user.email_verification_code != code:
            await message.answer("❌ Неверный код. Проверьте и введите снова.")
            return
        now = datetime.now(timezone.utc)
        expires_at = user.email_verification_expires_at
        if expires_at and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at and expires_at < now:
            await message.answer("❌ Код истёк. Начните заново: нажмите «Привязать email».")
            await state.finish()
            return
        user.email_verified = True
        user.email_verification_code = None
        user.email_verification_expires_at = None
        session.commit()

        from utils.menu_manager import get_menu_manager
        menu_manager = get_menu_manager()
        await menu_manager.return_to_menu(
            message, state,
            f"✅ Email <b>{email}</b> успешно привязан!\n\nТеперь вы можете входить на <a href=\"{WEB_PORTAL_URL}\">веб-портал</a> для судей.",
            None
        )
    finally:
        session.close()
        await state.finish()


# ======== Записаться на турнир ========
async def process_sign_up(callback_query: types.CallbackQuery):
    """
    Выбираем месяц, чтобы записаться на турнир
    """
    session = SessionLocal()
    try:
        months_raw = session.query(Tournament.month).distinct().all()
        months = [m[0] for m in months_raw if m[0]]
        if not months:
            await callback_query.message.answer("❌ Нет доступных турниров для записи.")
            return
        keyboard = InlineKeyboardMarkup(row_width=3)
        for month in months:
            keyboard.insert(InlineKeyboardButton(month, callback_data=f'month_{month}'))
        keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data='back_to_main'))
        await callback_query.message.answer("📅 Выберите месяц:", reply_markup=keyboard)
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при выборе месяца: {e}")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
    finally:
        session.close()
        await callback_query.answer()


async def process_month(callback_query: types.CallbackQuery):
    """
    После выбора месяца показываем турниры этого месяца
    """
    selected_month = callback_query.data.split('_', 1)[1]
    session = SessionLocal()
    try:
        tournaments = session.query(Tournament).filter(Tournament.month == selected_month).order_by(Tournament.date).all()
        if tournaments:
            keyboard = InlineKeyboardMarkup(row_width=1)
            for tournament in tournaments:
                # Убираем time/ location
                # Формат: "дата_название"
                button_text = f"{tournament.date.strftime('%d.%m.%Y')}_{tournament.name}"
                # Заменяем '_' на пробелы
                button_text = button_text.replace('_', ' ')
                # Но callback_data пусть остаётся "tournament_ID"
                keyboard.add(InlineKeyboardButton(button_text, callback_data=f'tournament_{tournament.tournament_id}'))

            keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data='sign_up'))
            await callback_query.message.answer(f"🏆 Выберите турнир в {selected_month}:", reply_markup=keyboard)
        else:
            await callback_query.message.answer(f"❌ Нет турниров в {selected_month}.")
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при выборе турнира: {e}")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
    finally:
        session.close()
        await callback_query.answer()


async def process_tournament(callback_query: types.CallbackQuery):
    """
    Когда судья нажимает на конкретный турнир, создаем заявку
    """
    tournament_id = int(callback_query.data.split('_')[-1])
    session = SessionLocal()
    try:
        tournament = session.query(Tournament).filter(Tournament.tournament_id == tournament_id).first()
        user = session.query(User).filter(User.user_id == callback_query.from_user.id).first()
        if not user or not tournament:
            await callback_query.message.answer("❌ Ошибка записи на турнир.")
            return

        existing_registration = session.query(Registration).filter(
            Registration.user_id == user.user_id,
            Registration.tournament_id == tournament.tournament_id
        ).first()
        if existing_registration:
            await callback_query.message.answer("ℹ️ Вы уже подали заявку на этот турнир.")
            return

        approved_count = session.query(Registration).filter(
            Registration.tournament_id == tournament.tournament_id,
            Registration.status == RegistrationStatus.APPROVED
        ).count()
        if approved_count >= MAX_JUDGES_PER_TOURNAMENT:
            await callback_query.message.answer(
                "❌ К сожалению, достигнуто максимальное количество судей на этот турнир."
            )
            return

        registration = Registration(
            user_id=user.user_id,
            tournament_id=tournament.tournament_id,
            status=RegistrationStatus.PENDING
        )
        session.add(registration)
        session.commit()

        logger.info(f"{user.first_name} {user.last_name} (ID: {user.user_id}) подал заявку на турнир {tournament.name}")

        # Логируем действие
        action_logger = get_action_logger()
        if action_logger:
            await action_logger.log_action(
                ActionType.USER_SIGNUP_TOURNAMENT,
                user.user_id,
                {"tournament": tournament.name, "date": tournament.date.strftime('%d.%m.%Y')}
            )

        # Выводим в виде "DD.MM.YYYY Название"
        tournament_str = f"{tournament.date.strftime('%d.%m.%Y')} {tournament.name}"

        await callback_query.message.answer(
            f"✅ {user.first_name} {user.last_name}, ваша заявка на судейство турнира "
            f"<b>{tournament_str}</b> отправлена и ожидает подтверждения.",
            parse_mode=ParseMode.HTML
        )

        if CHANNEL_ID:
            # словарь перевода
            STATUS_I18N = {
                RegistrationStatus.PENDING:  "На рассмотрении",
                RegistrationStatus.APPROVED: "Одобрено",
                RegistrationStatus.REJECTED: "Отклонено"
            }
            status_text = STATUS_I18N.get(registration.status, registration.status)

            await callback_query.bot.send_message(
                CHANNEL_ID,
                "🔔 <b>Новая заявка</b>\n"
                f"👤 <b>{user.first_name} {user.last_name}</b>\n"
                f"Турнир: <b>{tournament_str}</b>\n"
                f"Статус: {status_text}",
                parse_mode=ParseMode.HTML
            )

        if ADMIN_EMAIL:
            try:
                from api.email_service import send_new_registration_to_admin_email
                user_name = f"{user.first_name} {user.last_name}"
                send_new_registration_to_admin_email(ADMIN_EMAIL, user_name, tournament_str)
            except Exception as e:
                logger.exception("Ошибка отправки email админу о новой заявке: %s", e)

    except SQLAlchemyError as e:
        logger.error(f"Ошибка при записи на турнир: {e}")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
        # Отправляем ошибку в мониторинг
        error_monitor = get_error_monitor()
        if error_monitor:
            await error_monitor.log_critical_error(e, "process_tournament", callback_query.from_user.id)
    finally:
        session.close()
        await callback_query.answer()


# ======== Отмена записи ========
async def process_cancel_registration(callback_query: types.CallbackQuery):
    """
    Пользователь нажал «Отменить запись»
    """
    session = SessionLocal()
    try:
        user_id = callback_query.from_user.id
        months_raw = session.query(Tournament.month).join(Registration).filter(
            Registration.user_id == user_id
        ).distinct().all()
        months = [m[0] for m in months_raw if m[0]]

        if not months:
            await callback_query.message.answer("❌ У вас нет записей на турниры.")
            return

        keyboard = InlineKeyboardMarkup(row_width=3)
        for month in months:
            keyboard.insert(InlineKeyboardButton(month, callback_data=f'cancel_reg_month_{month}'))
        keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data='back_to_main'))

        await callback_query.message.answer("Выберите месяц, в котором хотите отменить запись:", reply_markup=keyboard)
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при отмене записи: {e}")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
    finally:
        session.close()
        await callback_query.answer()


async def process_cancel_reg_month(callback_query: types.CallbackQuery):
    selected_month = callback_query.data.split('_')[-1]
    session = SessionLocal()
    try:
        user_id = callback_query.from_user.id
        registrations = session.query(Registration).join(Tournament).filter(
            Registration.user_id == user_id,
            Tournament.month == selected_month
        ).all()

        if not registrations:
            await callback_query.message.answer(f"❌ У вас нет записей в {selected_month}.")
            return

        keyboard = InlineKeyboardMarkup()
        for reg in registrations:
            t = reg.tournament
            # формат: "Дата Название"
            button_text = f"{t.date.strftime('%d.%m.%Y')} {t.name}"
            keyboard.add(InlineKeyboardButton(button_text, callback_data=f'cancel_reg_id_{reg.registration_id}'))
        keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data='cancel_registration'))

        await callback_query.message.answer("Выберите турнир, запись на который нужно отменить:", reply_markup=keyboard)

    except SQLAlchemyError as e:
        logger.error(f"Ошибка: {e}")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
    finally:
        session.close()
        await callback_query.answer()


async def process_cancel_reg_id(callback_query: types.CallbackQuery):
    reg_id = int(callback_query.data.split('_')[-1])
    session = SessionLocal()
    try:
        registration = session.query(Registration).options(joinedload(Registration.tournament)).options(joinedload(Registration.user)).filter(
            Registration.registration_id == reg_id
        ).first()
        if not registration:
            await callback_query.message.answer("❌ Запись не найдена.")
            return

        t = registration.tournament
        user = registration.user
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("✅ Да", callback_data=f'confirm_cancel_{reg_id}'),
            InlineKeyboardButton("❌ Нет", callback_data='cancel_action')
        )
        await callback_query.message.answer(
            f"❗ Подтвердите отмену записи на турнир <b>{t.date.strftime('%d.%m.%Y')} {t.name}</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
    except SQLAlchemyError as e:
        logger.error(f"Ошибка: {e}")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
    finally:
        session.close()
        await callback_query.answer()


async def process_confirm_cancel(callback_query: types.CallbackQuery):
    reg_id = int(callback_query.data.split('_')[-1])
    session = SessionLocal()
    try:
        registration = session.query(Registration).options(joinedload(Registration.tournament)).options(joinedload(Registration.user)).filter(
            Registration.registration_id == reg_id
        ).first()
        if not registration:
            await callback_query.message.answer("❌ Запись не найдена.")
            return

        user = registration.user
        t = registration.tournament
        old_status = registration.status
        
        # Удаляем запись об оплате, если она существует
        from models import JudgePayment
        payment = session.query(JudgePayment).filter(
            JudgePayment.user_id == user.user_id,
            JudgePayment.tournament_id == t.tournament_id
        ).first()
        if payment:
            session.delete(payment)
            logger.info(f"Удалена запись об оплате для судьи {user.first_name} {user.last_name} (ID: {user.user_id}) на турнир {t.tournament_id}")

        session.delete(registration)
        session.commit()

        logger.info(f"{user.first_name} {user.last_name} (ID: {user.user_id}) отменил запись на турнир ID: {t.tournament_id}")

        await callback_query.message.answer(
            f"✅ Ваша запись на турнир <b>{t.date.strftime('%d.%m.%Y')} {t.name}</b> отменена.",
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu()
        )

        if CHANNEL_ID:
            # словарь перевода
            STATUS_I18N = {
                RegistrationStatus.PENDING:  "На рассмотрении",
                RegistrationStatus.APPROVED: "Одобрено",
                RegistrationStatus.REJECTED: "Отклонено"
            }
            status_text = STATUS_I18N.get(registration.status, registration.status)
            await callback_query.bot.send_message(
                CHANNEL_ID,
                f"ℹ️ <b>{user.first_name} {user.last_name}</b> отменил запись на турнир "
                f"<b>{t.date.strftime('%d.%m.%Y')} {t.name}</b> (предыдущий статус: {status_text}).",
                parse_mode=ParseMode.HTML
            )
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при отмене записи {reg_id}: {e}")
        await callback_query.message.answer("❌ Произшла ошибка. Попробуйте позже.")
    finally:
        session.close()
        await callback_query.answer()


async def process_cancel_action(callback_query: types.CallbackQuery, state: FSMContext):
    from utils.menu_manager import get_menu_manager
    menu_manager = get_menu_manager()
    await menu_manager.return_to_menu(
        callback_query, state,
        "✅ Отмена записи отменена.",
        ActionType.USER_CANCEL_REGISTRATION
    )


# ======== Мои записи ========
async def my_registrations_step(callback_query: types.CallbackQuery):
    session = SessionLocal()
    try:
        months_raw = session.query(Tournament.month).join(Registration).filter(
            Registration.user_id == callback_query.from_user.id
        ).distinct().all()
        months = [m[0] for m in months_raw if m[0]]
        if not months:
            await callback_query.message.answer("❌ У вас нет записей на турниры.")
            return
        keyboard = InlineKeyboardMarkup(row_width=3)
        for month in months:
            keyboard.insert(InlineKeyboardButton(month, callback_data=f'my_registrations_month_{month}'))
        keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data='back_to_main'))
        await callback_query.message.answer("📅 Выберите месяц для просмотра ваших записей:", reply_markup=keyboard)
        await MyRegistrations.waiting_for_month.set()
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при выборе месяца для просмотра записей: {e}")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
    finally:
        session.close()
        await callback_query.answer()


async def process_my_registrations_month(callback_query: types.CallbackQuery, state: FSMContext):
    selected_month = callback_query.data.split('_')[-1]
    session = SessionLocal()
    try:
        regs = session.query(Registration).join(Tournament).filter(
            Registration.user_id == callback_query.from_user.id,
            Tournament.month == selected_month
        ).all()
        if not regs:
            await callback_query.message.answer(f"❌ У вас нет записей на турниры в {selected_month}.")
            await state.finish()
            return

        message_text = f"📄 <b>Ваши записи на турниры в {selected_month}:</b>\n\n"
        for reg in regs:
            t = reg.tournament
            status_text = {
                RegistrationStatus.PENDING: '⏳ Ожидает',
                RegistrationStatus.APPROVED: '✅ Утверждена',
                RegistrationStatus.REJECTED: '❌ Отклонена'
            }.get(reg.status, 'Неизвестно')

            message_text += (
                f"🏆 <b>{t.date.strftime('%d.%m.%Y')} - {t.name}</b>\n"  # Убрали location/time
                f"🔖 Статус: {status_text}\n\n"
            )

        chunks = split_text(message_text, MAX_MESSAGE_LENGTH)
        for part in chunks:
            await callback_query.message.answer(part, parse_mode=ParseMode.HTML)

        await state.finish()
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при получении записей пользователя: {e}")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
    finally:
        session.close()
        await callback_query.answer()


# ======== Reply-кнопка «Вызвать главное меню» ========
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher.filters import Text

def main_reply_keyboard():
    """
    Создаёт Reply-клавиатуру с кнопкой "Вызвать главное меню".
    """
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("Вызвать главное меню"))
    return kb

async def handle_main_menu_button(message: types.Message):
    """
    Когда пользователь нажимает кнопку "Вызвать главное меню" (Reply-кнопка),
    выводим инлайн-меню (или что-то ещё).
    """
    await message.answer("Главное меню!", reply_markup=main_menu())

def setup_main_menu_button_handlers(dp):
    dp.register_message_handler(handle_main_menu_button, Text(equals="Вызвать главное меню"))

# ======== Система заработка ========
async def process_my_earnings(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Мой заработок'"""
    # Завершаем состояние PaymentAmount или CorrectEarnings если оно активно
    current_state = await state.get_state()
    if current_state and (current_state.startswith("PaymentAmount") or current_state.startswith("CorrectEarnings")):
        from utils.fsm_guard import get_fsm_guard
        fsm_guard = get_fsm_guard()
        fsm_guard.end_session(callback_query.from_user.id)
        await state.finish()
    
    from keyboards import earnings_menu_keyboard
    
    await callback_query.message.answer(
        "💰 <b>Мой заработок</b>\n\n"
        "Выберите, какую информацию вы хотите увидеть:",
        parse_mode=ParseMode.HTML,
        reply_markup=earnings_menu_keyboard()
    )
    await callback_query.answer()

async def process_earnings_detailed(callback_query: types.CallbackQuery, state: FSMContext):
    """Подробная информация о заработке"""
    # Завершаем состояние PaymentAmount если оно активно
    current_state = await state.get_state()
    if current_state and current_state.startswith("PaymentAmount"):
        from utils.fsm_guard import get_fsm_guard
        fsm_guard = get_fsm_guard()
        fsm_guard.end_session(callback_query.from_user.id)
        await state.finish()
    
    from services.payment_system import get_payment_system
    
    payment_system = get_payment_system(callback_query.bot)
    earnings_data = payment_system.get_judge_earnings(callback_query.from_user.id)
    
    if earnings_data['total_tournaments'] == 0:
        await callback_query.message.answer(
            "📊 <b>Заработок подробно</b>\n\n"
            "❌ У вас пока нет оплаченных турниров.\n"
            "Заработок появится после подтверждения оплаты за судейство.",
            parse_mode=ParseMode.HTML
        )
        await callback_query.answer()
        return
    
    message = "📊 <b>Заработок подробно</b>\n\n"
    
    # Общая статистика
    message += f"🏆 <b>Всего турниров:</b> {earnings_data['total_tournaments']}\n"
    message += f"💰 <b>Общая сумма:</b> {earnings_data['total_amount']:.2f} руб.\n\n"
    
    # Детальная информация по турнирам
    if earnings_data['tournament_earnings']:
        message += "📋 <b>Детали по турнирам:</b>\n"
        for tournament_name, tournament_date, amount, payment_date in earnings_data['tournament_earnings']:
            if amount:
                message += f"• {tournament_date.strftime('%d.%m.%Y')} - {tournament_name}\n"
                message += f"  💰 {amount:.2f} руб. (оплачено {payment_date.strftime('%d.%m.%Y')})\n\n"
            else:
                message += f"• {tournament_date.strftime('%d.%m.%Y')} - {tournament_name}\n"
                message += f"  💰 Сумма не указана (оплачено {payment_date.strftime('%d.%m.%Y')})\n\n"
    
    # Заработок по месяцам
    if earnings_data['monthly_earnings']:
        message += "📅 <b>Заработок по месяцам:</b>\n"
        for month, total_amount, tournaments_count in earnings_data['monthly_earnings']:
            message += f"• {month}: {total_amount:.2f} руб. ({tournaments_count} турниров)\n"
    
    # Разбиваем длинное сообщение на части
    from services.excel_export import split_text
    chunks = split_text(message, MAX_MESSAGE_LENGTH)
    for part in chunks:
        await callback_query.message.answer(part, parse_mode=ParseMode.HTML)
    
    await callback_query.answer()

async def process_earnings_summary(callback_query: types.CallbackQuery, state: FSMContext):
    """Краткий обзор заработка"""
    # Завершаем состояние PaymentAmount если оно активно
    current_state = await state.get_state()
    if current_state and current_state.startswith("PaymentAmount"):
        from utils.fsm_guard import get_fsm_guard
        fsm_guard = get_fsm_guard()
        fsm_guard.end_session(callback_query.from_user.id)
        await state.finish()
    from services.payment_system import get_payment_system
    
    payment_system = get_payment_system(callback_query.bot)
    earnings_data = payment_system.get_judge_earnings(callback_query.from_user.id)
    
    if earnings_data['total_tournaments'] == 0:
        await callback_query.message.answer(
            "📈 <b>Краткий обзор</b>\n\n"
            "❌ У вас пока нет оплаченных турниров.\n"
            "Заработок появится после подтверждения оплаты за судейство.",
            parse_mode=ParseMode.HTML
        )
    else:
        # Определяем рейтинг судьи
        if earnings_data['total_tournaments'] >= 50:
            rating = "🥇 Золотой судья"
        elif earnings_data['total_tournaments'] >= 25:
            rating = "🥈 Серебряный судья"
        elif earnings_data['total_tournaments'] >= 10:
            rating = "🥉 Бронзовый судья"
        else:
            rating = "⭐ Начинающий судья"
        
        message = (
            "📈 <b>Краткий обзор</b>\n\n"
            f"🏆 <b>Отсужено турниров:</b> {earnings_data['total_tournaments']}\n"
            f"💰 <b>Общий заработок:</b> {earnings_data['total_amount']:.2f} руб.\n"
            f"📊 <b>Средний заработок:</b> {earnings_data['total_amount'] / earnings_data['total_tournaments']:.2f} руб./турнир\n\n"
            f"🎖️ <b>Ваш рейтинг:</b> {rating}\n\n"
            f"💡 Для подробной информации выберите «Заработок подробно»"
        )
        
        await callback_query.message.answer(message, parse_mode=ParseMode.HTML)
    
    await callback_query.answer()

async def process_payment_yes(callback_query: types.CallbackQuery, state: FSMContext):
    """Судья подтвердил оплату"""
    try:
        payment_id = int(callback_query.data.split('_')[-1])
        
        # Создаем клавиатуру с кнопкой отмены
        from keyboards import InlineKeyboardMarkup, InlineKeyboardButton
        cancel_keyboard = InlineKeyboardMarkup()
        cancel_keyboard.add(InlineKeyboardButton("❌ Отменить", callback_data='cancel_payment_input'))
        cancel_keyboard.add(InlineKeyboardButton("🔙 В главное меню", callback_data='back_to_main'))
        
        await callback_query.message.answer(
            "💰 <b>Отлично!</b>\n\n"
            "А сколько вам заплатили? Введите сумму и отправьте сообщением (только число):\n\n"
            "<i>Минимальная сумма: 3500 рублей</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=cancel_keyboard
        )
        
        # Сохраняем ID платежа в состоянии
        from states import PaymentAmount
        await PaymentAmount.waiting_for_amount.set()
        await state.update_data(payment_id=payment_id)
        
        # Регистрируем сессию в FSM Guard
        from utils.fsm_guard import get_fsm_guard
        fsm_guard = get_fsm_guard()
        fsm_guard.start_session(callback_query.from_user.id, "PaymentAmount", state)
        
        await callback_query.answer()
        
    except (ValueError, IndexError) as e:
        logger.error(f"Ошибка в process_payment_yes: {e}")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Неожиданная ошибка в process_payment_yes: {e}")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
        await callback_query.answer()

async def process_payment_no(callback_query: types.CallbackQuery):
    """Судья сообщил, что не получил оплату"""
    try:
        from services.payment_system import get_payment_system
        
        payment_id = int(callback_query.data.split('_')[-1])
        payment_system = get_payment_system(callback_query.bot)
        
        await payment_system.handle_payment_confirmation(payment_id, False)
        
        await callback_query.message.answer(
            "😔 <b>Понятно...</b>\n\n"
            "Мы уведомили администратора о том, что оплата не поступила.\n"
            "Надеемся, что ситуация скоро решится! 🤞",
            parse_mode=ParseMode.HTML
        )
        
        await callback_query.answer()
        
    except (ValueError, IndexError) as e:
        logger.error(f"Ошибка в process_payment_no: {e}")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Неожиданная ошибка в process_payment_no: {e}")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
        await callback_query.answer()

async def process_payment_amount(message: types.Message, state: FSMContext):
    """Обработка введенной суммы оплаты"""
    try:
        if not message.text:
            await message.answer("❌ Пожалуйста, отправьте текстовое сообщение.")
            return
            
        amount = float(message.text.strip().replace(',', '.'))
        if amount <= 0:
            await message.answer("❌ Сумма должна быть больше нуля. Попробуйте еще раз:")
            return
        
        # Проверка минимальной суммы оплаты
        MIN_PAYMENT_AMOUNT = 3500
        if amount < MIN_PAYMENT_AMOUNT:
            await message.answer(
                f"❌ Минимальная сумма оплаты составляет {MIN_PAYMENT_AMOUNT} рублей.\n"
                f"Вы ввели {amount} рублей. Пожалуйста, введите корректную сумму:"
            )
            return
        
        # Получаем ID платежа из callback_data (нужно будет передать через состояние)
        # Пока что используем простой подход - ищем последний неоплаченный платеж пользователя
        from services.payment_system import get_payment_system
        from database import SessionLocal
        from models import JudgePayment
        
        session = SessionLocal()
        try:
            # Получаем сохраненный ID платежа из состояния
            data = await state.get_data()
            payment_id = data.get('payment_id')
            
            if not payment_id:
                await message.answer("❌ Не найдена запись об оплате. Обратитесь к администратору.")
                await state.finish()
                return
            
            # Проверяем, что платеж принадлежит пользователю и не оплачен
            payment = session.query(JudgePayment).filter(
                JudgePayment.payment_id == payment_id,
                JudgePayment.user_id == message.from_user.id,
                JudgePayment.is_paid == False
            ).first()
            
            if not payment:
                await message.answer("❌ Не найдена запись об оплате. Обратитесь к администратору.")
                await state.finish()
                return
            
            # Обрабатываем подтверждение оплаты
            payment_system = get_payment_system(message.bot)
            await payment_system.handle_payment_confirmation(payment_id, True, amount)
            
            # Завершаем FSM сессию
            from utils.fsm_guard import get_fsm_guard
            fsm_guard = get_fsm_guard()
            fsm_guard.end_session(message.from_user.id)
            
            await message.answer(
                "✅ <b>Спасибо!</b> Информация об оплате сохранена.",
                parse_mode=ParseMode.HTML
            )
            
        finally:
            session.close()
            
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректную сумму (например: 3500 или 5000.50):")
        return
    except Exception as e:
        logger.error(f"Неожиданная ошибка в process_payment_amount: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")
    
    await state.finish()

# ======== Исправление заработка ========
async def process_correct_earnings(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Исправить заработок'"""
    # Завершаем состояние PaymentAmount если оно активно
    current_state = await state.get_state()
    if current_state and current_state.startswith("PaymentAmount"):
        from utils.fsm_guard import get_fsm_guard
        fsm_guard = get_fsm_guard()
        fsm_guard.end_session(callback_query.from_user.id)
        await state.finish()
    
    session = SessionLocal()
    try:
        user_id = callback_query.from_user.id
        
        # Получаем оплаченные записи судьи
        from models import JudgePayment
        paid_payments = session.query(JudgePayment).filter(
            and_(
                JudgePayment.user_id == user_id,
                JudgePayment.is_paid == True
            )
        ).join(Tournament).order_by(Tournament.date.desc()).limit(20).all()
        
        if not paid_payments:
            await callback_query.message.answer(
                "❌ У вас нет оплаченных записей для исправления.",
                parse_mode=ParseMode.HTML
            )
            await callback_query.answer()
            return
        
        # Создаем клавиатуру с турнирами
        keyboard = InlineKeyboardMarkup(row_width=1)
        for payment in paid_payments:
            amount_text = f"{payment.amount} руб." if payment.amount else "сумма не указана"
            button_text = f"{payment.tournament.date.strftime('%d.%m.%Y')} - {payment.tournament.name} ({amount_text})"
            keyboard.add(InlineKeyboardButton(button_text, callback_data=f'correct_earnings_tournament_{payment.payment_id}'))
        
        keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data='my_earnings'))
        
        await callback_query.message.answer(
            "✏️ <b>Исправление заработка</b>\n\n"
            "Выберите турнир, для которого хотите исправить заработок:",
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
        
        await callback_query.answer()
    except (DatabaseError, sqlite3.DatabaseError) as e:
        error_msg = str(e)
        if "malformed" in error_msg.lower():
            logger.critical(f"База данных повреждена в process_correct_earnings: {e}")
            await callback_query.message.answer(
                "❌ <b>База данных повреждена</b>\n\n"
                "Требуется восстановление базы данных.\n"
                "Обратитесь к администратору.",
                parse_mode=ParseMode.HTML
            )
        else:
            logger.error(f"Ошибка базы данных в process_correct_earnings: {e}")
            await callback_query.message.answer("❌ Произошла ошибка базы данных. Попробуйте позже.")
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Ошибка в process_correct_earnings: {e}")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
        await callback_query.answer()
    finally:
        session.close()

async def process_correct_earnings_tournament(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработка выбора турнира для исправления заработка"""
    payment_id = int(callback_query.data.split('_')[-1])
    session = SessionLocal()
    try:
        from models import JudgePayment
        payment = session.query(JudgePayment).options(
            joinedload(JudgePayment.user),
            joinedload(JudgePayment.tournament)
        ).filter(JudgePayment.payment_id == payment_id).first()
        
        if not payment:
            await callback_query.message.answer("❌ Запись об оплате не найдена.")
            await callback_query.answer()
            return
        
        # Проверяем, что это запись текущего пользователя
        if payment.user_id != callback_query.from_user.id:
            await callback_query.message.answer("❌ Это не ваша запись об оплате.")
            await callback_query.answer()
            return
        
        if not payment.is_paid:
            await callback_query.message.answer("❌ Эта запись еще не оплачена.")
            await callback_query.answer()
            return
        
        # Специальная проверка для Лизочки Марковой
        is_special_judge = payment.user_id == 946719504
        
        current_amount = payment.amount if payment.amount else "не указана"
        
        if is_special_judge:
            message_text = (
                f"✏️ <b>Исправление заработка</b>\n\n"
                f"Турнир: <b>{payment.tournament.name}</b>\n"
                f"Дата: {payment.tournament.date.strftime('%d.%m.%Y')}\n"
                f"Текущая сумма: {current_amount} руб.\n\n"
                f"Введите правильную сумму заработка (индивидуальная сумма):"
            )
        else:
            message_text = (
                f"✏️ <b>Исправление заработка</b>\n\n"
                f"Турнир: <b>{payment.tournament.name}</b>\n"
                f"Дата: {payment.tournament.date.strftime('%d.%m.%Y')}\n"
                f"Текущая сумма: {current_amount} руб.\n"
                f"Стандартная сумма: 5000 руб.\n\n"
                f"Введите правильную сумму заработка:"
            )
        
        # Создаем клавиатуру с кнопкой отмены
        cancel_keyboard = InlineKeyboardMarkup()
        cancel_keyboard.add(InlineKeyboardButton("❌ Отменить", callback_data='my_earnings'))
        
        await callback_query.message.answer(message_text, parse_mode=ParseMode.HTML, reply_markup=cancel_keyboard)
        
        await state.update_data(payment_id=payment_id, is_special_judge=is_special_judge)
        await CorrectEarnings.waiting_for_amount.set()
        
        # Регистрируем сессию в FSM Guard
        from utils.fsm_guard import get_fsm_guard
        fsm_guard = get_fsm_guard()
        fsm_guard.start_session(callback_query.from_user.id, "CorrectEarnings", state)
        
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Ошибка в process_correct_earnings_tournament: {e}")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
        await callback_query.answer()
    finally:
        session.close()

async def process_correct_earnings_amount(message: types.Message, state: FSMContext):
    """Обработка введенной суммы для исправления заработка"""
    try:
        if not message.text:
            await message.answer("❌ Пожалуйста, отправьте текстовое сообщение.")
            return
        
        amount = float(message.text.strip().replace(',', '.'))
        if amount <= 0:
            await message.answer("❌ Сумма должна быть больше нуля. Попробуйте еще раз:")
            return
        
        data = await state.get_data()
        payment_id = data.get('payment_id')
        is_special_judge = data.get('is_special_judge', False)
        
        if not payment_id:
            await message.answer("❌ Не найдена запись об оплате. Обратитесь к администратору.")
            await state.finish()
            return
        
        session = SessionLocal()
        try:
            from models import JudgePayment
            payment = session.query(JudgePayment).options(
                joinedload(JudgePayment.user),
                joinedload(JudgePayment.tournament)
            ).filter(JudgePayment.payment_id == payment_id).first()
            
            if not payment:
                await message.answer("❌ Запись об оплате не найдена.")
                await state.finish()
                return
            
            # Проверяем, что это запись текущего пользователя
            if payment.user_id != message.from_user.id:
                await message.answer("❌ Это не ваша запись об оплате.")
                await state.finish()
                return
            
            # Проверка минимальной суммы (только для обычных судей)
            MIN_PAYMENT_AMOUNT = 3500
            if not is_special_judge and amount < MIN_PAYMENT_AMOUNT:
                await message.answer(
                    f"❌ Минимальная сумма оплаты составляет {MIN_PAYMENT_AMOUNT} рублей.\n"
                    f"Вы ввели {amount} рублей. Пожалуйста, введите корректную сумму:"
                )
                return
            
            # Проверка стандартной суммы (только для обычных судей)
            STANDARD_PAYMENT_AMOUNT = 5000
            if not is_special_judge and amount != STANDARD_PAYMENT_AMOUNT:
                await message.answer(
                    f"⚠️ Внимание! Стандартная сумма для всех судей (кроме Лизочки Марковой) составляет {STANDARD_PAYMENT_AMOUNT} руб.\n"
                    f"Вы ввели {amount} руб.\n\n"
                    f"Продолжить с этой суммой? (введите 'да' для подтверждения или новую сумму):"
                )
                await state.update_data(pending_amount=amount)
                return
            
            # Если была попытка ввести нестандартную сумму, проверяем подтверждение
            pending_amount = data.get('pending_amount')
            if pending_amount and message.text.lower() not in ['да', 'yes', 'y', 'д']:
                try:
                    new_amount = float(message.text.strip().replace(',', '.'))
                    amount = new_amount
                    await state.update_data(pending_amount=None)
                except ValueError:
                    await message.answer("❌ Ввод отменен. Используйте /start для возврата в меню.")
                    await state.finish()
                    return
            
            # Обновляем сумму
            old_amount = payment.amount
            payment.amount = amount
            session.commit()
            
            # Завершаем FSM сессию
            from utils.fsm_guard import get_fsm_guard
            fsm_guard = get_fsm_guard()
            fsm_guard.end_session(message.from_user.id)
            
            await message.answer(
                f"✅ <b>Заработок успешно исправлен!</b>\n\n"
                f"💰 Старая сумма: {old_amount if old_amount else 'не указана'} руб.\n"
                f"💰 Новая сумма: {amount} руб.\n"
                f"📅 Дата: {payment.tournament.date.strftime('%d.%m.%Y')}\n"
                f"🏆 Турнир: {payment.tournament.name}",
                parse_mode=ParseMode.HTML
            )
            
            # Логируем действие
            action_logger = get_action_logger()
            if action_logger:
                await action_logger.log_action(
                    ActionType.USER_EDIT_PROFILE,
                    f"Судья {payment.user.first_name} {payment.user.last_name} исправил заработок с {old_amount} на {amount} руб. за турнир {payment.tournament.name}"
                )
            
        finally:
            session.close()
        
        await state.finish()
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректную сумму (например: 5000 или 5000.50):")
        return
    except Exception as e:
        logger.error(f"Неожиданная ошибка в process_correct_earnings_amount: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")
        await state.finish()
