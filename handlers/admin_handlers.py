import logging
import asyncio
from datetime import datetime, date

from aiogram import types
from aiogram.dispatcher import FSMContext
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from database import SessionLocal
from models import User, Tournament, Registration, RegistrationStatus, JudgePayment
from states import (
    AddTournament, EditTournament, SendAllMessages,
    CheckRegistrations, DeleteTournament, ManualPaymentInput
)
from keyboards import admin_menu_keyboard
from config import ADMIN_IDS, MAX_MESSAGE_LENGTH, MAX_JUDGES_PER_TOURNAMENT
from services.excel_export import export_data, split_text
from utils.calendar import build_calendar, prev_month, next_month  # <- твой модуль календаря
from utils.error_monitor import get_error_monitor
from utils.action_logger import get_action_logger, ActionType
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode

logger = logging.getLogger(__name__)


# ========== Вспомогательные функции ==========
async def send_tournament_change_notification(bot, users, old_tournament, new_tournament):
    """
    Отправляет детальное уведомление об изменении турнира всем пользователям
    """
    changes = []
    
    # Проверяем изменения в дате
    if old_tournament.date != new_tournament.date:
        old_date_str = old_tournament.date.strftime('%d.%m.%Y')
        new_date_str = new_tournament.date.strftime('%d.%m.%Y')
        changes.append(f"📅 <b>Дата:</b> {old_date_str} → {new_date_str}")
    
    # Проверяем изменения в названии
    if old_tournament.name != new_tournament.name:
        changes.append(f"🏆 <b>Название:</b> {old_tournament.name} → {new_tournament.name}")
    
    # Проверяем изменения в месяце
    if old_tournament.month != new_tournament.month:
        changes.append(f"📆 <b>Месяц:</b> {old_tournament.month} → {new_tournament.month}")
    
    if not changes:
        return  # Нет изменений
    
    # Формируем сообщение
    message = f"🔄 <b>Турнир изменен</b>\n\n"
    message += f"🏆 <b>Турнир:</b> {new_tournament.date.strftime('%d.%m.%Y')} {new_tournament.name}\n\n"
    message += f"📝 <b>Изменения:</b>\n"
    for change in changes:
        message += f"• {change}\n"
    
    # Отправляем всем пользователям батчами для оптимизации
    batch_size = 50  # Отправляем по 50 пользователей за раз
    for i in range(0, len(users), batch_size):
        batch = users[i:i + batch_size]
        tasks = []
        for user in batch:
            task = bot.send_message(user.user_id, message, parse_mode="HTML")
            tasks.append(task)
        
        # Выполняем все задачи в батче параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обрабатываем ошибки
        for j, result in enumerate(results):
            if isinstance(result, Exception):
                user = batch[j]
                logger.error("Failed to send tournament change notification to user %s: %s", user.user_id, result)
                # Отправляем ошибку в мониторинг
                error_monitor = get_error_monitor()
                if error_monitor:
                    await error_monitor.log_warning(
                        f"Failed to send tournament change notification",
                        f"user_id={user.user_id}, tournament_id={new_tournament.tournament_id}",
                        user.user_id
                    )
        
        # Пауза между батчами
        if i + batch_size < len(users):
            await asyncio.sleep(1)


# ========== /admin — Главное меню для админа ==========
async def cmd_admin(message: types.Message, state: FSMContext):
    logger.info("[cmd_admin] called by user_id=%s", message.from_user.id)
    if message.from_user.id not in ADMIN_IDS:
        logger.warning("[cmd_admin] access denied for user_id=%s", message.from_user.id)
        await message.answer("❌ У вас нет доступа к административным функциям.")
        return

    # Сбрасываем FSM состояние при входе в админку, чтобы кнопки работали
    await state.finish()

    # Устанавливаем контекст пользователя как админ
    from utils.menu_manager import get_menu_manager
    menu_manager = get_menu_manager()
    menu_manager.set_user_context(message.from_user.id, "admin")

    await message.answer("🛠️ Административное меню:", reply_markup=admin_menu_keyboard())
    logger.info("[cmd_admin] menu shown")


async def admin_actions(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Ловит все callback с префиксом admin_ (в main зарегистрирован).
    """
    data = callback_query.data
    uid = callback_query.from_user.id
    logger.info("[admin_actions] data=%s, user_id=%s", data, uid)

    if uid not in ADMIN_IDS:
        await callback_query.message.answer("❌ У вас нет доступа к административным функциям.")
        await callback_query.answer()
        return

    if data == 'admin_add_tournament':
        await add_tournament_step(callback_query)
    elif data == 'admin_view_referees':
        await view_referees(callback_query)
    elif data == 'admin_view_tournaments':
        await view_tournaments(callback_query)
    elif data == 'admin_edit_tournament':
        await edit_tournament_step(callback_query)
    elif data == 'admin_check_registrations':
        await check_registrations_step(callback_query)
    elif data == 'admin_export_data':
        await export_data_step(callback_query)
    elif data == 'admin_sendall':
        await admin_sendall_action(callback_query)
    elif data == 'admin_review_registrations':
        await admin_review_registrations(callback_query)
    elif data == 'admin_delete_tournament':
        await delete_tournament_step(callback_query)
    # admin_judge_earnings теперь обрабатывается в main.py
    # back_to_admin_main теперь обрабатывается в main.py
    else:
        await callback_query.message.answer("❓ Неизвестная команда.")

    await callback_query.answer()


# ========== Добавление турнира ==========
async def add_tournament_step(callback_query: types.CallbackQuery):
    months = [
        "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ]
    kb = InlineKeyboardMarkup(row_width=3)
    for m in months:
        kb.insert(InlineKeyboardButton(m, callback_data=f'add_tournament_month_{m}'))
    kb.add(InlineKeyboardButton("⬅️ Назад", callback_data='admin_menu'))
    await callback_query.message.answer("📅 Выберите месяц для турнира:", reply_markup=kb)
    await AddTournament.waiting_for_month.set()
    await callback_query.answer()


async def process_add_tournament_month(callback_query: types.CallbackQuery, state: FSMContext):
    selected_month = callback_query.data.split('_')[-1]
    await state.update_data(month=selected_month)

    # Покажем календарь с текущим месяцем (твой build_calendar принимает текущую дату/месяц)
    await callback_query.message.answer("🗓️ Выберите дату турнира:", reply_markup=build_calendar())
    await AddTournament.waiting_for_date.set()
    await callback_query.answer()


async def process_add_tournament_date(message: types.Message, state: FSMContext):
    """
    Альтернативный путь, если дату ввели ручным текстом.
    """
    date_str = message.text.strip()
    try:
        date_obj = datetime.strptime(date_str, '%d.%m.%Y').date()
        
        # Проверяем, что дата не в прошлом
        if date_obj < datetime.now().date():
            await message.answer("❌ Дата турнира не может быть в прошлом! Введите корректную дату:")
            return
            
    except ValueError:
        await message.answer("❌ Неверный формат даты. Введите ДД.ММ.ГГГГ:")
        return
    await state.update_data(date=date_obj)
    await message.answer("🏆 Введите название турнира:")
    await AddTournament.next()


async def calendar_callbacks(callback_query: types.CallbackQuery, state: FSMContext):
    data = (callback_query.data or "").strip()
    uid = callback_query.from_user.id
    logger.info("[calendar_callbacks] data=%s user=%s", data, uid)

    if data.startswith("cal_prev_"):
        try:
            parts = data.split("_")
            if len(parts) != 4:
                raise ValueError("Invalid callback data format")
            _, _, y, m = parts
            y, m = int(y), int(m)
            if not (1 <= m <= 12) or y < 2020:
                raise ValueError("Invalid date values")
            ny, nm = prev_month(y, m)
            await callback_query.message.edit_reply_markup(build_calendar((ny, nm)))
            return await callback_query.answer()
        except (ValueError, IndexError) as e:
            logger.error(f"cal_prev failed: {data}, error: {e}")
            return await callback_query.answer("⚠️ Ошибка листания назад", show_alert=True)
        except Exception:
            logger.exception("cal_prev failed")
            return await callback_query.answer("⚠️ Ошибка листания назад", show_alert=True)

    if data.startswith("cal_next_"):
        try:
            parts = data.split("_")
            if len(parts) != 4:
                raise ValueError("Invalid callback data format")
            _, _, y, m = parts
            y, m = int(y), int(m)
            if not (1 <= m <= 12) or y < 2020:
                raise ValueError("Invalid date values")
            ny, nm = next_month(y, m)
            await callback_query.message.edit_reply_markup(build_calendar((ny, nm)))
            return await callback_query.answer()
        except (ValueError, IndexError) as e:
            logger.error(f"cal_next failed: {data}, error: {e}")
            return await callback_query.answer("⚠️ Ошибка листания вперёд", show_alert=True)
        except Exception:
            logger.exception("cal_next failed")
            return await callback_query.answer("⚠️ Ошибка листания вперёд", show_alert=True)

    # Выбор дня — НОВЫЙ формат
    if data.startswith("cal_pick_"):
        try:
            _, _, y, m, d = data.split("_")
            year, month, day = int(y), int(m), int(d)
            
            # Валидация даты
            if not (2020 <= year <= 2030):
                raise ValueError("Invalid year")
            if not (1 <= month <= 12):
                raise ValueError("Invalid month")
            if not (1 <= day <= 31):
                raise ValueError("Invalid day")
                
            picked = date(year, month, day)
            
            # Дополнительная проверка на существование даты
            if picked.month != month or picked.day != day:
                raise ValueError("Invalid date")
                
            current_state = await state.get_state()
            
            if current_state == "AddTournament:waiting_for_date":
                await state.update_data(date=picked)
                await callback_query.message.edit_text(
                    f"📅 Дата выбрана: <b>{picked.strftime('%d.%m.%Y')}</b>\n\n"
                    f"🏆 Введите название турнира:",
                    parse_mode=ParseMode.HTML
                )
                from states import AddTournament
                await AddTournament.waiting_for_name.set()
            elif current_state == "EditTournament:waiting_for_new_date":
                await state.update_data(new_date=picked)
                await callback_query.message.edit_text(
                    f"📅 Новая дата выбрана: <b>{picked.strftime('%d.%m.%Y')}</b>\n\n"
                    f"🏆 Введите новое название турнира:",
                    parse_mode=ParseMode.HTML
                )
                from states import EditTournament
                await EditTournament.waiting_for_new_name.set()
            else:
                await state.update_data(date=picked)
                await callback_query.message.edit_text(
                    f"📅 Дата выбрана: <b>{picked.strftime('%d.%m.%Y')}</b>",
                    parse_mode=ParseMode.HTML
                )
            
            return await callback_query.answer("Дата выбрана")
        except (ValueError, IndexError) as e:
            logger.error(f"Invalid date format: {data}, error: {e}")
            return await callback_query.answer("❌ Неверная дата", show_alert=True)
        except Exception as e:
            logger.exception(f"cal_pick failed: {data}, error: {e}")
            return await callback_query.answer("⚠️ Ошибка при выборе даты", show_alert=True)

    # Выбор дня — СТАРЫЙ формат (на всякий случай)
    if data.startswith("cal_day_"):
        try:
            _, _, y, m, d = data.split("_")
            picked = date(int(y), int(m), int(d))
            await state.update_data(date=picked)
            await callback_query.message.edit_text(
                f"📅 Дата выбрана: <b>{picked.strftime('%d.%m.%Y')}</b>\n\n"
                f"🏆 Введите название турнира:",
                parse_mode=ParseMode.HTML
            )
            from states import AddTournament
            await AddTournament.waiting_for_name.set()
            return await callback_query.answer("Дата выбрана")
        except Exception:
            logger.exception("cal_day failed")
            return await callback_query.answer("⚠️ Ошибка при выборе даты", show_alert=True)

    if data == "cal_cancel":
        await callback_query.message.edit_text("Окей, отменил выбор даты.")
        return await callback_query.answer("Отменено")

    if data == "cal_nop":
        # Пустая ячейка/шапка
        return await callback_query.answer(" ")

    # Диагностика неожиданных данных
    logger.warning("[calendar_callbacks] Unknown calendar cb: %s", data)
    return await callback_query.answer("Неизвестная команда календаря", show_alert=False)


async def process_add_tournament_name(message: types.Message, state: FSMContext):
    name = (message.text or "").strip()
    if not name:
        await message.answer("❌ Поле не может быть пустым. Введите название турнира:")
        return

    session = SessionLocal()
    data = await state.get_data()
    try:
        tournament = Tournament(
            month=data['month'],
            date=data['date'],
            name=name
        )
        session.add(tournament)
        session.commit()

        # Создаем записи об оплате для всех утвержденных судей (если есть)
        from services.payment_system import get_payment_system
        payment_system = get_payment_system(message.bot)
        await payment_system.create_payment_records(tournament.tournament_id)

        formatted = f"{tournament.date.strftime('%d.%m.%Y')} {tournament.name}"
        from utils.menu_manager import get_menu_manager
        menu_manager = get_menu_manager()
        await menu_manager.return_to_menu(
            message, state,
            f"✅ Турнир <b>{formatted}</b> добавлен в <b>{tournament.month}</b>.",
            ActionType.ADMIN_ADD_TOURNAMENT
        )

        # Уведомим всех пользователей
        referees = session.query(User).all()
        for ref in referees:
            try:
                await message.bot.send_message(
                    ref.user_id,
                    f"🆕 Добавлен турнир <b>{formatted}</b> в <b>{tournament.month}</b>.",
                    parse_mode=ParseMode.HTML
                )
                await asyncio.sleep(0.05)
            except Exception as e:
                logger.error("Notify failed user_id=%s: %s", ref.user_id, e)

    except SQLAlchemyError as e:
        logger.exception("DB error on add tournament")
        await message.answer("❌ Ошибка при добавлении турнира. Попробуйте позже.")
        # Отправляем ошибку в мониторинг
        error_monitor = get_error_monitor()
        if error_monitor:
            await error_monitor.log_critical_error(e, "process_add_tournament_name", message.from_user.id)
    finally:
        session.close()
        await state.finish()


# ========== Просмотр судей ==========
async def view_referees(callback_query: types.CallbackQuery):
    session = SessionLocal()
    try:
        referees = session.query(User).order_by(User.last_name, User.first_name).all()
        if referees:
            msg = "<b>Зарегистрированные судьи:</b>\n\n"
            for ref in referees:
                msg += (
                    f"👤 <b>{ref.first_name} {ref.last_name}</b>\n"
                    f"🔧 Функция: {ref.function}\n"
                    f"🏅 Категория: {ref.category}\n"
                    f"🆔 ID: {ref.user_id}\n\n"
                )
        else:
            msg = "❌ Нет зарегистрированных судей."

        for part in split_text(msg, MAX_MESSAGE_LENGTH):
            await callback_query.message.answer(part, parse_mode=ParseMode.HTML)
    except SQLAlchemyError:
        logger.exception("DB error in view_referees")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
    finally:
        session.close()
        await callback_query.answer()


# ========== Просмотр турниров (по месяцам) ==========
async def view_tournaments(callback_query: types.CallbackQuery):
    session = SessionLocal()
    try:
        months = session.query(Tournament.month).distinct().all()
        if not months:
            await callback_query.message.answer("❌ Нет созданных турниров.")
            return

        kb = InlineKeyboardMarkup(row_width=3)
        for m in months:
            kb.insert(InlineKeyboardButton(m[0], callback_data=f'view_tournaments_month_{m[0]}'))
        kb.add(InlineKeyboardButton("⬅️ Назад", callback_data='admin_menu'))

        await callback_query.message.answer("Выберите месяц, чтобы посмотреть турниры:", reply_markup=kb)
    except SQLAlchemyError:
        logger.exception("DB error in view_tournaments")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
    finally:
        session.close()
        await callback_query.answer()


async def process_view_tournaments_month(callback_query: types.CallbackQuery):
    selected_month = callback_query.data.split('_')[-1]
    session = SessionLocal()
    try:
        tournaments = session.query(Tournament).filter(Tournament.month == selected_month).order_by(Tournament.date).all()
        if not tournaments:
            await callback_query.message.answer(f"❌ Нет турниров в {selected_month}.")
            return

        msg = f"<b>Турниры в {selected_month}:</b>\n\n"
        for t in tournaments:
            msg += f"   - <b>{t.date.strftime('%d.%m.%Y')} {t.name}</b>\n"

        await callback_query.message.answer(msg, parse_mode=ParseMode.HTML)
    except SQLAlchemyError:
        logger.exception("DB error in process_view_tournaments_month")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
    finally:
        session.close()
        await callback_query.answer()


# ========== Изменение турнира ==========
async def edit_tournament_step(callback_query: types.CallbackQuery):
    session = SessionLocal()
    try:
        months = session.query(Tournament.month).distinct().all()
        if not months:
            await callback_query.message.answer("❌ Нет доступных турниров для изменения.")
            return
        kb = InlineKeyboardMarkup(row_width=3)
        for m in months:
            kb.insert(InlineKeyboardButton(m[0], callback_data=f'edit_tournament_month_{m[0]}'))
        kb.add(InlineKeyboardButton("⬅️ Назад", callback_data='admin_menu'))
        await callback_query.message.answer("📅 Выберите месяц турнира для изменения:", reply_markup=kb)
        await EditTournament.waiting_for_month.set()
    except SQLAlchemyError:
        logger.exception("DB error in edit_tournament_step")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
    finally:
        session.close()
        await callback_query.answer()


async def process_edit_tournament_month(callback_query: types.CallbackQuery, state: FSMContext):
    selected_month = callback_query.data.split('_')[-1]
    session = SessionLocal()
    try:
        tournaments = session.query(Tournament).filter(Tournament.month == selected_month).order_by(Tournament.date).all()
        if tournaments:
            kb = InlineKeyboardMarkup(row_width=1)
            for tour in tournaments:
                btn_text = f"{tour.date.strftime('%d.%m.%Y')} {tour.name}"
                kb.add(InlineKeyboardButton(btn_text, callback_data=f'edit_tournament_{tour.tournament_id}'))
            kb.add(InlineKeyboardButton("⬅️ Назад", callback_data='admin_edit_tournament'))
            await callback_query.message.answer(
                f"🏆 Выберите турнир в {selected_month} для изменения:",
                reply_markup=kb
            )
            await state.update_data(month=selected_month)
            await EditTournament.waiting_for_tournament_selection.set()
        else:
            await callback_query.message.answer(f"❌ Нет турниров в {selected_month}.")
            await state.finish()
    except SQLAlchemyError:
        logger.exception("DB error in process_edit_tournament_month")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
    finally:
        session.close()
        await callback_query.answer()


async def process_edit_tournament_selection(callback_query: types.CallbackQuery, state: FSMContext):
    tournament_id = int(callback_query.data.split('_')[-1])
    await state.update_data(tournament_id=tournament_id)
    await callback_query.message.answer("🗓️ Выберите новую дату турнира:", reply_markup=build_calendar())
    await EditTournament.waiting_for_new_date.set()
    await callback_query.answer()


# Удален - теперь используется календарь


async def process_edit_tournament_new_name(message: types.Message, state: FSMContext):
    name = (message.text or "").strip()
    if not name:
        await message.answer("❌ Поле не может быть пустым. Введите название турнира:")
        return

    session = SessionLocal()
    data = await state.get_data()
    try:
        tournament = session.query(Tournament).filter(Tournament.tournament_id == data['tournament_id']).first()
        if tournament:
            # Сохраняем старые данные для сравнения
            old_tournament = Tournament(
                tournament_id=tournament.tournament_id,
                month=tournament.month,
                date=tournament.date,
                name=tournament.name
            )
            
            # Обновляем турнир
            tournament.date = data['new_date']
            tournament.name = name
            session.commit()

            updated = f"{tournament.date.strftime('%d.%m.%Y')} {tournament.name}"
            from utils.menu_manager import get_menu_manager
            menu_manager = get_menu_manager()
            await menu_manager.return_to_menu(
                message, state,
                f"✅ Турнир <b>{updated}</b> успешно изменен.",
                ActionType.ADMIN_EDIT_TOURNAMENT
            )
            
            # Отправляем детальные уведомления всем пользователям
            users = session.query(User).all()
            await send_tournament_change_notification(message.bot, users, old_tournament, tournament)
        else:
            await message.answer("❌ Турнир не найден.")
    except SQLAlchemyError as e:
        logger.exception("DB error in process_edit_tournament_new_name")
        await message.answer("❌ Произошла ошибка при изменении турнира.")
        # Отправляем ошибку в мониторинг
        error_monitor = get_error_monitor()
        if error_monitor:
            await error_monitor.log_critical_error(e, "process_edit_tournament_new_name", message.from_user.id)
    finally:
        session.close()
        await state.finish()


# ========== Проверка записей ==========
async def check_registrations_step(callback_query: types.CallbackQuery):
    session = SessionLocal()
    try:
        months = session.query(Tournament.month).distinct().all()
        if not months:
            await callback_query.message.answer("❌ Нет доступных турниров.")
            return

        kb = InlineKeyboardMarkup(row_width=3)
        for m in months:
            kb.insert(InlineKeyboardButton(m[0], callback_data=f'check_registrations_month_{m[0]}'))
        kb.add(InlineKeyboardButton("⬅️ Назад", callback_data='admin_menu'))

        await callback_query.message.answer("📅 Выберите месяц для проверки записей:", reply_markup=kb)
        await CheckRegistrations.waiting_for_month.set()
    except SQLAlchemyError:
        logger.exception("DB error in check_registrations_step")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
    finally:
        session.close()
        await callback_query.answer()


async def process_check_registrations_month(callback_query: types.CallbackQuery, state: FSMContext):
    selected_month = callback_query.data.split('_')[-1]
    session = SessionLocal()
    try:
        tournaments = session.query(Tournament).filter(Tournament.month == selected_month).order_by(Tournament.date).all()
        if not tournaments:
            await callback_query.message.answer(f"❌ Нет турниров в {selected_month}.")
            await state.finish()
            return

        response = f"📋 <b>Турниры за {selected_month}:</b>\n\n"
        for t in tournaments:
            response += f"🏆 <b>{t.date.strftime('%d.%m.%Y')} {t.name}</b>\n"
            regs = session.query(Registration).join(User).filter(Registration.tournament_id == t.tournament_id).order_by(User.last_name, User.first_name).all()
            if regs:
                for reg in regs:
                    u = reg.user
                    status_text = {
                        RegistrationStatus.PENDING: '⏳ Ожидает',
                        RegistrationStatus.APPROVED: '✅ Утверждена',
                        RegistrationStatus.REJECTED: '❌ Отклонена'
                    }.get(reg.status, 'Неизвестно')
                    response += f"   - {status_text} | 👤 {u.first_name} {u.last_name} (ID: {u.user_id})\n"
            else:
                response += "   - Нет зарегистрированных судей.\n"
            response += "\n"

        for part in split_text(response, MAX_MESSAGE_LENGTH):
            await callback_query.message.answer(part, parse_mode=ParseMode.HTML)
        await state.finish()
    except SQLAlchemyError:
        logger.exception("DB error in process_check_registrations_month")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
    finally:
        session.close()
        await callback_query.answer()


# ========== Экспорт ==========
async def export_data_step(callback_query: types.CallbackQuery):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("📅 За месяц", callback_data='export_period_month'),
        InlineKeyboardButton("📆 За год", callback_data='export_period_year'),
        InlineKeyboardButton("🎓 За сезон (сентябрь–июнь)", callback_data='export_period_season'),
        InlineKeyboardButton("🗓️ За всё время", callback_data='export_period_all'),
        InlineKeyboardButton("⬅️ Назад", callback_data='admin_menu'),
    )
    await callback_query.message.answer("📊 Выберите период для выгрузки данных:", reply_markup=kb)
    await callback_query.answer()


async def process_export_period(callback_query: types.CallbackQuery):
    period = callback_query.data.split('_')[-1]
    logger.info(f"Обработка экспорта за период: {period}")
    
    if period == 'month':
        await select_month_for_export(callback_query)
    elif period == 'year':
        await select_year_for_export(callback_query)
    elif period == 'season':
        logger.info("Запуск экспорта за сезон...")
        await export_data(callback_query.bot, callback_query, period='season')
    elif period == 'all':
        await export_data(callback_query.bot, callback_query, period='all')
    else:
        await callback_query.message.answer("❌ Неверный период.")
    await callback_query.answer()


async def select_month_for_export(callback_query: types.CallbackQuery):
    months = [
        "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ]
    kb = InlineKeyboardMarkup(row_width=3)
    for m in months:
        kb.insert(InlineKeyboardButton(m, callback_data=f'export_month_{m}'))
    kb.add(InlineKeyboardButton("⬅️ Назад", callback_data='admin_export_data'))
    await callback_query.message.answer("📅 Выберите месяц для выгрузки данных:", reply_markup=kb)


async def process_export_month(callback_query: types.CallbackQuery):
    selected_month = callback_query.data.split('_')[-1]
    await export_data(callback_query.bot, callback_query, period='month', month=selected_month)
    await callback_query.answer()


async def select_year_for_export(callback_query: types.CallbackQuery):
    current_year = datetime.now().year
    years = [str(y) for y in range(current_year - 5, current_year + 2)]
    kb = InlineKeyboardMarkup(row_width=3)
    for y in years:
        kb.insert(InlineKeyboardButton(y, callback_data=f'export_year_{y}'))
    kb.add(InlineKeyboardButton("⬅️ Назад", callback_data='admin_export_data'))
    await callback_query.message.answer("📆 Выберите год для выгрузки данных:", reply_markup=kb)


async def process_export_year(callback_query: types.CallbackQuery):
    selected_year = int(callback_query.data.split('_')[-1])
    await export_data(callback_query.bot, callback_query, period='year', year=selected_year)
    await callback_query.answer()


# ========== Удаление турнира ==========
async def delete_tournament_step(callback_query: types.CallbackQuery):
    months = [
        "Январь","Февраль","Март","Апрель","Май","Июнь",
        "Июль","Август","Сентябрь","Октябрь","Ноябрь","Декабрь"
    ]
    kb = InlineKeyboardMarkup(row_width=3)
    for m in months:
        kb.insert(InlineKeyboardButton(m, callback_data=f'delete_month_{m}'))
    kb.add(InlineKeyboardButton("⬅️ Назад", callback_data='back_to_admin_main'))
    await callback_query.message.answer("📅 Выберите месяц для удаления турнира:", reply_markup=kb)
    await DeleteTournament.waiting_for_month.set()
    await callback_query.answer()


async def process_delete_month(cb: types.CallbackQuery, state: FSMContext):
    month = cb.data.split('_', 2)[-1]
    await state.update_data(month=month)
    session = SessionLocal()
    try:
        tours = session.query(Tournament).filter(Tournament.month == month).all()
    finally:
        session.close()

    if not tours:
        await cb.message.edit_text(f"❌ Турниров за {month} не найдено.", reply_markup=None)
        return await state.finish()

    kb = InlineKeyboardMarkup(row_width=1)
    for t in tours:
        txt = f"{t.date.strftime('%d.%m.%Y')} {t.name}"
        kb.add(InlineKeyboardButton(txt, callback_data=f'delete_tournament_{t.tournament_id}'))
    kb.add(InlineKeyboardButton("⬅️ Назад", callback_data='admin_delete_tournament'))

    await cb.message.edit_text("🏆 Выберите турнир для удаления:", reply_markup=kb)
    await DeleteTournament.waiting_for_tournament_selection.set()
    await cb.answer()


async def process_delete_tournament(cb: types.CallbackQuery, state: FSMContext):
    tourn_id = int(cb.data.split('_')[-1])
    await state.update_data(tournament_id=tourn_id)
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Да, удалить", callback_data='delete_confirm_yes'),
        InlineKeyboardButton("❌ Отмена", callback_data='delete_confirm_no')
    )
    await cb.message.edit_text("⚠️ Вы уверены, что хотите удалить этот турнир?", reply_markup=kb)
    await DeleteTournament.waiting_for_confirmation.set()
    await cb.answer()


async def process_delete_confirm(cb: types.CallbackQuery, state: FSMContext):
    choice = cb.data.split('_')[-1]
    data = await state.get_data()

    if choice == 'yes':
        session = SessionLocal()
        try:
            t = session.query(Tournament).get(data['tournament_id'])
            if not t:
                await cb.message.edit_text("❌ Турнир не найден.", reply_markup=None)
                await state.finish()
                return
            title = f"{t.date.strftime('%d.%m.%Y')} {t.name}"
            month = data.get('month', '')
            tournament_id = t.tournament_id
            
            # Удаляем связанные данные в правильном порядке
            from models import Registration, JudgePayment, TournamentBudget
            
            try:
                # 1. Удаляем записи об оплате
                payments_deleted = session.query(JudgePayment).filter(
                    JudgePayment.tournament_id == tournament_id
                ).delete(synchronize_session=False)
                
                # 2. Удаляем регистрации
                registrations_deleted = session.query(Registration).filter(
                    Registration.tournament_id == tournament_id
                ).delete(synchronize_session=False)
                
                # 3. Удаляем бюджет турнира
                budgets_deleted = session.query(TournamentBudget).filter(
                    TournamentBudget.tournament_id == tournament_id
                ).delete(synchronize_session=False)
                
                # 4. Удаляем сам турнир
                session.delete(t)
                session.commit()
                
                logger.info(f"Удален турнир {tournament_id}: платежей={payments_deleted}, регистраций={registrations_deleted}, бюджетов={budgets_deleted}")

                # Уведомим всех (Telegram + email)
                for u in session.query(User).all():
                    try:
                        await cb.message.bot.send_message(u.user_id, f"❗️ Турнир «{title}» ({month}) удалён админом.")
                    except Exception as e:
                        logger.error("Failed to notify user %s about tournament deletion: %s", u.user_id, e)
                    if u.email:
                        try:
                            from api.email_service import send_tournament_deleted_email
                            send_tournament_deleted_email(u.email, title, month)
                        except Exception as e:
                            logger.exception("Ошибка email об удалении турнира для %s: %s", u.email, e)

                # Логируем действие
                action_logger = get_action_logger()
                if action_logger:
                    await action_logger.log_action(
                        ActionType.ADMIN_DELETE_TOURNAMENT,
                        cb.from_user.id,
                        {"tournament": title, "month": month}
                    )

                await cb.message.edit_text(f"✅ Турнир «{title}» удалён.", reply_markup=None)
                
            except SQLAlchemyError as e:
                session.rollback()
                logger.exception(f"Ошибка БД при удалении турнира {tournament_id}: {e}")
                await cb.message.edit_text(
                    f"❌ Ошибка при удалении турнира «{title}». "
                    f"Попробуйте позже или используйте скрипт delete_tournament_force.py",
                    reply_markup=None
                )
                # Отправляем ошибку в мониторинг
                error_monitor = get_error_monitor()
                if error_monitor:
                    await error_monitor.log_error(
                        f"Ошибка при удалении турнира {tournament_id}",
                        str(e),
                        cb.from_user.id
                    )
            except Exception as e:
                session.rollback()
                logger.exception(f"Неожиданная ошибка при удалении турнира {tournament_id}: {e}")
                await cb.message.edit_text(
                    f"❌ Произошла неожиданная ошибка при удалении турнира «{title}». "
                    f"Попробуйте позже или используйте скрипт delete_tournament_force.py",
                    reply_markup=None
                )
        finally:
            session.close()
    else:
        await cb.message.edit_text("ℹ️ Удаление отменено.", reply_markup=None)

    await state.finish()
    await cb.answer()


# ========== Массовая рассылка ==========
async def admin_sendall_action(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.message.answer("❌ У вас нет доступа к этой функции.")
        await callback_query.answer()
        return

    await callback_query.message.answer("📢 Введите сообщение, которое вы хотите отправить всем пользователям:")
    await SendAllMessages.waiting_for_message.set()
    await callback_query.answer()


async def process_sendall_message(message: types.Message, state: FSMContext):
    admin_message = (message.text or "").strip()
    if not admin_message:
        await message.answer("❌ Сообщение не может быть пустым. Пожалуйста, введите текст:")
        return

    await message.answer("📤 Начинаю отправку сообщения всем пользователям...")
    await state.finish()

    session = SessionLocal()
    try:
        users = session.query(User).all()
        total, ok, fail = len(users), 0, 0
        for u in users:
            try:
                await message.bot.send_message(u.user_id, admin_message, parse_mode=ParseMode.HTML)
                ok += 1
                await asyncio.sleep(0.1)  # Увеличиваем задержку для безопасности
            except Exception as e:
                logger.error("Broadcast fail to user_id=%s: %s", u.user_id, e)
                fail += 1

        await message.answer(
            f"✅ Сообщение отправлено.\nВсего: {total}\nУспешно: {ok}\nНе удалось: {fail}"
        )
    except SQLAlchemyError:
        logger.exception("DB error in process_sendall_message")
        await message.answer("❌ Произошла ошибка при рассылке.")
    finally:
        session.close()


# ========== Рассмотрение заявок ==========
async def admin_review_registrations(callback_query: types.CallbackQuery):
    session = SessionLocal()
    try:
        months = session.query(Tournament.month).distinct().all()
        if not months:
            await callback_query.message.answer("❌ Нет доступных турниров.")
            return
        kb = InlineKeyboardMarkup(row_width=3)
        for m in months:
            kb.insert(InlineKeyboardButton(m[0], callback_data=f'review_month_{m[0]}'))
        kb.add(InlineKeyboardButton("⬅️ Назад", callback_data='admin_menu'))
        await callback_query.message.answer("📅 Выберите месяц для рассмотрения заявок:", reply_markup=kb)
    except SQLAlchemyError:
        logger.exception("DB error in admin_review_registrations")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
    finally:
        session.close()
        await callback_query.answer()


async def admin_review_tournaments_in_month(callback_query: types.CallbackQuery):
    selected_month = callback_query.data.split('_')[-1]
    session = SessionLocal()
    try:
        tournaments = session.query(Tournament).filter(Tournament.month == selected_month).order_by(Tournament.date).all()
        if not tournaments:
            await callback_query.message.answer(f"❌ Нет турниров в {selected_month}.")
            return

        kb = InlineKeyboardMarkup(row_width=1)
        for t in tournaments:
            btn_text = f"{t.date.strftime('%d.%m.%Y')} {t.name}"
            kb.add(InlineKeyboardButton(btn_text, callback_data=f'review_tournament_{t.tournament_id}'))
        kb.add(InlineKeyboardButton("⬅️ Назад", callback_data='admin_review_registrations'))

        await callback_query.message.answer(f"📋 Турниры в {selected_month}:", reply_markup=kb)
    except SQLAlchemyError:
        logger.exception("DB error in admin_review_tournaments_in_month")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
    finally:
        session.close()
        await callback_query.answer()


async def process_review_tournament(callback_query: types.CallbackQuery):
    tournament_id = int(callback_query.data.split('_')[-1])
    session = SessionLocal()
    try:
        registrations = session.query(Registration).options(joinedload(Registration.user)).join(User).filter(
            Registration.tournament_id == tournament_id,
            Registration.status == RegistrationStatus.PENDING
        ).order_by(User.last_name, User.first_name).all()
        if not registrations:
            await callback_query.message.answer("ℹ️ Нет заявок для рассмотрения.")
            return

        for reg in registrations:
            user = reg.user
            kb = InlineKeyboardMarkup()
            kb.add(
                InlineKeyboardButton("✅ Утвердить", callback_data=f'approve_{reg.registration_id}'),
                InlineKeyboardButton("❌ Отклонить", callback_data=f'reject_{reg.registration_id}')
            )
            msg_text = (
                f"👤 <b>{user.first_name} {user.last_name}</b>\n"
                f"🔧 Функция: {user.function}\n"
                f"🏅 Категория: {user.category}"
            )
            await callback_query.message.answer(msg_text, parse_mode=ParseMode.HTML, reply_markup=kb)

        back_kb = InlineKeyboardMarkup()
        # вернуться к списку турниров месяца
        month = registrations[0].tournament.month if registrations else ""
        back_kb.add(InlineKeyboardButton("⬅️ Назад", callback_data=f'review_month_{month}'))
        await callback_query.message.answer("Вы можете вернуться назад или в главное меню.", reply_markup=back_kb)
    except SQLAlchemyError:
        logger.exception("DB error in process_review_tournament")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
    finally:
        session.close()
        await callback_query.answer()


async def process_approve_registration(callback_query: types.CallbackQuery):
    registration_id = int(callback_query.data.split('_')[-1])
    session = SessionLocal()
    try:
        registration = session.query(Registration).options(
            joinedload(Registration.tournament),
            joinedload(Registration.user)
        ).get(registration_id)
        if not registration:
            await callback_query.answer("Заявка не найдена или уже обработана.", show_alert=True)
            return

        approved_count = session.query(Registration).filter(
            Registration.tournament_id == registration.tournament_id,
            Registration.status == RegistrationStatus.APPROVED
        ).count()
        if approved_count >= MAX_JUDGES_PER_TOURNAMENT:
            await callback_query.answer("Достигнуто максимальное количество судей (15).", show_alert=True)
            return

        if registration.status == RegistrationStatus.PENDING:
            registration.status = RegistrationStatus.APPROVED
            session.commit()

            # Создаем запись об оплате для утвержденного судьи
            from services.payment_system import get_payment_system
            payment_system = get_payment_system(callback_query.bot)
            await payment_system.create_payment_records(registration.tournament_id)

            u = registration.user
            t = registration.tournament
            await callback_query.answer("Заявка утверждена.")
            await callback_query.message.bot.send_message(
                u.user_id,
                f"✅ Вы утверждены для судейства турнира <b>{t.date.strftime('%d.%m.%Y')} {t.name}</b>!",
                parse_mode=ParseMode.HTML
            )
            if u.email:
                try:
                    from api.email_service import send_registration_approved_email
                    send_registration_approved_email(u.email, t.name, t.date.strftime('%d.%m.%Y'))
                    logger.info("Email approve отправлен на %s", u.email)
                except Exception as e:
                    logger.exception("Ошибка email approve: %s", e)
            else:
                logger.info("Email approve пропущен: у судьи user_id=%s нет email", u.user_id)
        else:
            await callback_query.answer("Заявка уже обработана.", show_alert=True)
    except SQLAlchemyError:
        logger.exception("DB error in process_approve_registration")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
    finally:
        session.close()


async def process_reject_registration(callback_query: types.CallbackQuery):
    registration_id = int(callback_query.data.split('_')[-1])
    session = SessionLocal()
    try:
        registration = session.query(Registration).options(
            joinedload(Registration.tournament),
            joinedload(Registration.user)
        ).get(registration_id)
        if not registration:
            await callback_query.answer("Заявка не найдена или уже обработана.", show_alert=True)
            return

        if registration.status == RegistrationStatus.PENDING:
            registration.status = RegistrationStatus.REJECTED
            session.commit()

            u = registration.user
            t = registration.tournament
            await callback_query.answer("Заявка отклонена.")
            await callback_query.message.bot.send_message(
                u.user_id,
                f"❌ Ваша заявка на судейство турнира <b>{t.date.strftime('%d.%m.%Y')} {t.name}</b> отклонена.",
                parse_mode=ParseMode.HTML
            )
            if u.email:
                try:
                    from api.email_service import send_registration_rejected_email
                    send_registration_rejected_email(u.email, t.name, t.date.strftime('%d.%m.%Y'))
                    logger.info("Email reject отправлен на %s", u.email)
                except Exception as e:
                    logger.exception("Ошибка email reject: %s", e)
            else:
                logger.info("Email reject пропущен: у судьи user_id=%s нет email", u.user_id)
        else:
            await callback_query.answer("Заявка уже обработана.", show_alert=True)
    except SQLAlchemyError:
        logger.exception("DB error in process_reject_registration")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
    finally:
        session.close()


# ========== Заработок судей ==========
async def admin_judge_earnings_menu(callback_query: types.CallbackQuery):
    """Меню заработка судей для админа"""
    from keyboards import admin_earnings_menu_keyboard
    
    await callback_query.message.answer(
        "💰 <b>Заработок судей</b>\n\n"
        "Выберите период для просмотра заработка:",
        parse_mode=ParseMode.HTML,
        reply_markup=admin_earnings_menu_keyboard()
    )
    await callback_query.answer()

async def admin_earnings_monthly(callback_query: types.CallbackQuery):
    """Выбор месяца для просмотра заработка"""
    session = SessionLocal()
    try:
        # Получаем все месяцы, в которых есть оплаченные турниры
        months = session.query(Tournament.month).join(
            JudgePayment, Tournament.tournament_id == JudgePayment.tournament_id
        ).filter(
            JudgePayment.is_paid == True
        ).distinct().order_by(Tournament.month).all()
        
        if not months:
            await callback_query.message.answer("❌ Нет данных о заработке судей.")
            return
        
        month_list = [month[0] for month in months]
        from keyboards import month_selection_earnings_keyboard
        await callback_query.message.answer(
            "📅 Выберите месяц для просмотра заработка:",
            reply_markup=month_selection_earnings_keyboard(month_list)
        )
    except SQLAlchemyError as e:
        logger.exception("DB error in admin_earnings_monthly")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
    finally:
        session.close()
    await callback_query.answer()

async def admin_earnings_yearly(callback_query: types.CallbackQuery):
    """Выбор года для просмотра заработка"""
    session = SessionLocal()
    try:
        # Получаем все годы, в которых есть оплаченные турниры
        from sqlalchemy import func
        years = session.query(
            func.strftime('%Y', Tournament.date).label('year')
        ).join(
            JudgePayment, Tournament.tournament_id == JudgePayment.tournament_id
        ).filter(
            JudgePayment.is_paid == True
        ).distinct().order_by('year').all()
        
        if not years:
            await callback_query.message.answer("❌ Нет данных о заработке судей.")
            return
        
        year_list = [int(year[0]) for year in years]
        from keyboards import year_selection_earnings_keyboard
        await callback_query.message.answer(
            "📆 Выберите год для просмотра заработка:",
            reply_markup=year_selection_earnings_keyboard(year_list)
        )
    except SQLAlchemyError as e:
        logger.exception("DB error in admin_earnings_yearly")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
    finally:
        session.close()
    await callback_query.answer()

async def admin_earnings_seasonal(callback_query: types.CallbackQuery):
    """Просмотр заработка за сезон"""
    session = SessionLocal()
    try:
        from sqlalchemy import func, and_
        from datetime import date
        
        # Определяем текущий сезон
        current_date = date.today()
        if current_date.month >= 9:  # Сентябрь и позже
            season_start = date(current_date.year, 9, 1)
            season_end = date(current_date.year + 1, 5, 31)
        else:  # До сентября
            season_start = date(current_date.year - 1, 9, 1)
            season_end = date(current_date.year, 5, 31)
        
        # Получаем заработок судей за сезон
        earnings = session.query(
            User.first_name,
            User.last_name,
            func.sum(JudgePayment.amount).label('total_amount'),
            func.count(JudgePayment.payment_id).label('tournaments_count')
        ).join(
            JudgePayment, User.user_id == JudgePayment.user_id
        ).join(
            Tournament, JudgePayment.tournament_id == Tournament.tournament_id
        ).filter(
            and_(
                JudgePayment.is_paid == True,
                Tournament.date >= season_start,
                Tournament.date <= season_end,
                JudgePayment.amount.isnot(None)
            )
        ).group_by(User.user_id).order_by(func.sum(JudgePayment.amount).desc()).all()
        
        if not earnings:
            await callback_query.message.answer(
                f"❌ Нет данных о заработке за сезон {season_start.year}-{season_end.year}."
            )
            return
        
        # Формируем сообщение
        message = f"💰 <b>Заработок судей за сезон {season_start.year}-{season_end.year}</b>\n\n"
        
        total_amount = 0
        for first_name, last_name, amount, tournaments_count in earnings:
            message += f"👤 <b>{first_name} {last_name}</b>\n"
            message += f"   💰 {amount:.2f} руб. ({tournaments_count} турниров)\n\n"
            total_amount += amount
        
        message += f"📊 <b>Итого:</b> {total_amount:.2f} руб."
        
        # Разбиваем длинное сообщение на части
        chunks = split_text(message, MAX_MESSAGE_LENGTH)
        for part in chunks:
            await callback_query.message.answer(part, parse_mode=ParseMode.HTML)
            
    except SQLAlchemyError as e:
        logger.exception("DB error in admin_earnings_seasonal")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
    finally:
        session.close()
    await callback_query.answer()

# ========== Ручной ввод заработка ==========
async def admin_manual_payment(callback_query: types.CallbackQuery):
    """Меню для ручного ввода заработка судьи"""
    session = SessionLocal()
    try:
        # Получаем список судей с неоплаченными записями
        unpaid_payments = session.query(JudgePayment).filter(
            JudgePayment.is_paid == False
        ).join(User).join(Tournament).order_by(Tournament.date.desc()).all()
        
        if not unpaid_payments:
            await callback_query.message.answer(
                "✅ Нет неоплаченных записей для ручного ввода.",
                parse_mode=ParseMode.HTML
            )
            await callback_query.answer()
            return
        
        # Группируем по судьям
        judges_dict = {}
        for payment in unpaid_payments:
            user_id = payment.user_id
            if user_id not in judges_dict:
                judges_dict[user_id] = {
                    'user': payment.user,
                    'payments': []
                }
            judges_dict[user_id]['payments'].append(payment)
        
        # Создаем клавиатуру с судьями
        keyboard = InlineKeyboardMarkup(row_width=1)
        for user_id, data in sorted(judges_dict.items(), key=lambda x: (x[1]['user'].last_name, x[1]['user'].first_name)):
            user = data['user']
            unpaid_count = len(data['payments'])
            button_text = f"{user.first_name} {user.last_name} ({unpaid_count} неоплачено)"
            keyboard.add(InlineKeyboardButton(button_text, callback_data=f'manual_payment_judge_{user_id}'))
        
        keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data='admin_menu'))
        
        await callback_query.message.answer(
            "💰 <b>Ручной ввод заработка</b>\n\n"
            "Выберите судью для ввода заработка:",
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Ошибка в admin_manual_payment: {e}")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
        await callback_query.answer()
    finally:
        session.close()

async def process_manual_payment_judge(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработка выбора судьи для ручного ввода заработка"""
    user_id = int(callback_query.data.split('_')[-1])
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user:
            await callback_query.message.answer("❌ Судья не найден.")
            await callback_query.answer()
            return
        
        # Получаем неоплаченные записи для этого судьи
        unpaid_payments = session.query(JudgePayment).filter(
            and_(
                JudgePayment.user_id == user_id,
                JudgePayment.is_paid == False
            )
        ).join(Tournament).order_by(Tournament.date.desc()).all()
        
        if not unpaid_payments:
            await callback_query.message.answer(
                f"✅ У {user.first_name} {user.last_name} нет неоплаченных записей.",
                parse_mode=ParseMode.HTML
            )
            await callback_query.answer()
            return
        
        # Создаем клавиатуру с турнирами
        keyboard = InlineKeyboardMarkup(row_width=1)
        for payment in unpaid_payments:
            button_text = f"{payment.tournament.date.strftime('%d.%m.%Y')} - {payment.tournament.name}"
            keyboard.add(InlineKeyboardButton(button_text, callback_data=f'manual_payment_tournament_{payment.payment_id}'))
        
        keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data='admin_manual_payment'))
        
        await callback_query.message.answer(
            f"💰 <b>Ручной ввод заработка</b>\n\n"
            f"Судья: <b>{user.first_name} {user.last_name}</b>\n\n"
            f"Выберите турнир для ввода заработка:",
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
        
        await state.update_data(judge_user_id=user_id)
        await ManualPaymentInput.waiting_for_tournament_selection.set()
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Ошибка в process_manual_payment_judge: {e}")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
        await callback_query.answer()
    finally:
        session.close()

async def process_manual_payment_tournament(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработка выбора турнира для ручного ввода заработка"""
    payment_id = int(callback_query.data.split('_')[-1])
    session = SessionLocal()
    try:
        payment = session.query(JudgePayment).options(
            joinedload(JudgePayment.user),
            joinedload(JudgePayment.tournament)
        ).filter(JudgePayment.payment_id == payment_id).first()
        
        if not payment:
            await callback_query.message.answer("❌ Запись об оплате не найдена.")
            await callback_query.answer()
            return
        
        if payment.is_paid:
            await callback_query.message.answer("❌ Эта запись уже оплачена.")
            await callback_query.answer()
            return
        
        # Специальная проверка для Лизочки Марковой
        is_special_judge = payment.user_id == 946719504
        
        if is_special_judge:
            message_text = (
                f"💰 <b>Ручной ввод заработка</b>\n\n"
                f"Судья: <b>{payment.user.first_name} {payment.user.last_name}</b>\n"
                f"Турнир: <b>{payment.tournament.name}</b>\n"
                f"Дата: {payment.tournament.date.strftime('%d.%m.%Y')}\n\n"
                f"Введите сумму заработка для этого судьи (индивидуальная сумма):"
            )
        else:
            message_text = (
                f"💰 <b>Ручной ввод заработка</b>\n\n"
                f"Судья: <b>{payment.user.first_name} {payment.user.last_name}</b>\n"
                f"Турнир: <b>{payment.tournament.name}</b>\n"
                f"Дата: {payment.tournament.date.strftime('%d.%m.%Y')}\n\n"
                f"Введите сумму заработка (стандартная: 5000 руб.):"
            )
        
        await callback_query.message.answer(message_text, parse_mode=ParseMode.HTML)
        
        await state.update_data(payment_id=payment_id, is_special_judge=is_special_judge)
        await ManualPaymentInput.waiting_for_amount.set()
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Ошибка в process_manual_payment_tournament: {e}")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
        await callback_query.answer()
    finally:
        session.close()

async def process_manual_payment_amount(message: types.Message, state: FSMContext):
    """Обработка введенной суммы заработка"""
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
            # Сохраняем сумму для подтверждения
            await state.update_data(pending_amount=amount)
            return
        
        # Если была попытка ввести нестандартную сумму, проверяем подтверждение
        pending_amount = data.get('pending_amount')
        if pending_amount and message.text.lower() not in ['да', 'yes', 'y', 'д']:
            # Пользователь ввел новую сумму или отменил
            try:
                new_amount = float(message.text.strip().replace(',', '.'))
                amount = new_amount
                await state.update_data(pending_amount=None)
            except ValueError:
                await message.answer("❌ Ввод отменен. Используйте /admin для возврата в меню.")
                await state.finish()
                return
        
        # Получаем информацию о платеже для логирования
        session = SessionLocal()
        try:
            payment = session.query(JudgePayment).options(
                joinedload(JudgePayment.user),
                joinedload(JudgePayment.tournament)
            ).filter(JudgePayment.payment_id == payment_id).first()
            
            if not payment:
                await message.answer("❌ Запись об оплате не найдена.")
                await state.finish()
                return
            
            # Сохраняем заработок
            from services.payment_system import get_payment_system
            payment_system = get_payment_system(message.bot)
            await payment_system.handle_payment_confirmation(payment_id, True, amount)
            
            await message.answer(
                f"✅ <b>Заработок успешно введен!</b>\n\n"
                f"💰 Сумма: {amount} руб.\n"
                f"📅 Дата: {payment.tournament.date.strftime('%d.%m.%Y')}\n"
                f"🏆 Турнир: {payment.tournament.name}",
                parse_mode=ParseMode.HTML
            )
            
            # Логируем действие
            action_logger = get_action_logger()
            if action_logger:
                await action_logger.log_action(
                    ActionType.ADMIN_MANUAL_PAYMENT,
                    f"Админ вручную ввел заработок {amount} руб. для судьи {payment.user.first_name} {payment.user.last_name} за турнир {payment.tournament.name}"
                )
        finally:
            session.close()
        
        await state.finish()
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректную сумму (например: 5000 или 5000.50):")
        return
    except Exception as e:
        logger.error(f"Неожиданная ошибка в process_manual_payment_amount: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")
        await state.finish()

async def process_earnings_month(callback_query: types.CallbackQuery):
    """Просмотр заработка за конкретный месяц"""
    selected_month = callback_query.data.split('_')[-1]
    session = SessionLocal()
    try:
        from sqlalchemy import func, and_
        
        # Получаем заработок судей за месяц
        earnings = session.query(
            User.first_name,
            User.last_name,
            func.sum(JudgePayment.amount).label('total_amount'),
            func.count(JudgePayment.payment_id).label('tournaments_count')
        ).join(
            JudgePayment, User.user_id == JudgePayment.user_id
        ).join(
            Tournament, JudgePayment.tournament_id == Tournament.tournament_id
        ).filter(
            and_(
                JudgePayment.is_paid == True,
                Tournament.month == selected_month,
                JudgePayment.amount.isnot(None)
            )
        ).group_by(User.user_id).order_by(func.sum(JudgePayment.amount).desc()).all()
        
        if not earnings:
            await callback_query.message.answer(f"❌ Нет данных о заработке за {selected_month}.")
            return
        
        # Формируем сообщение
        message = f"💰 <b>Заработок судей за {selected_month}</b>\n\n"
        
        total_amount = 0
        for first_name, last_name, amount, tournaments_count in earnings:
            message += f"👤 <b>{first_name} {last_name}</b>\n"
            message += f"   💰 {amount:.2f} руб. ({tournaments_count} турниров)\n\n"
            total_amount += amount
        
        message += f"📊 <b>Итого:</b> {total_amount:.2f} руб."
        
        # Разбиваем длинное сообщение на части
        chunks = split_text(message, MAX_MESSAGE_LENGTH)
        for part in chunks:
            await callback_query.message.answer(part, parse_mode=ParseMode.HTML)
            
    except SQLAlchemyError as e:
        logger.exception("DB error in process_earnings_month")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
    finally:
        session.close()
    await callback_query.answer()

async def process_earnings_year(callback_query: types.CallbackQuery):
    """Просмотр заработка за конкретный год"""
    selected_year = int(callback_query.data.split('_')[-1])
    session = SessionLocal()
    try:
        from sqlalchemy import func, and_
        
        # Получаем заработок судей за год
        earnings = session.query(
            User.first_name,
            User.last_name,
            func.sum(JudgePayment.amount).label('total_amount'),
            func.count(JudgePayment.payment_id).label('tournaments_count')
        ).join(
            JudgePayment, User.user_id == JudgePayment.user_id
        ).join(
            Tournament, JudgePayment.tournament_id == Tournament.tournament_id
        ).filter(
            and_(
                JudgePayment.is_paid == True,
                func.strftime('%Y', Tournament.date) == str(selected_year),
                JudgePayment.amount.isnot(None)
            )
        ).group_by(User.user_id).order_by(func.sum(JudgePayment.amount).desc()).all()
        
        if not earnings:
            await callback_query.message.answer(f"❌ Нет данных о заработке за {selected_year} год.")
            return
        
        # Формируем сообщение
        message = f"💰 <b>Заработок судей за {selected_year} год</b>\n\n"
        
        total_amount = 0
        for first_name, last_name, amount, tournaments_count in earnings:
            message += f"👤 <b>{first_name} {last_name}</b>\n"
            message += f"   💰 {amount:.2f} руб. ({tournaments_count} турниров)\n\n"
            total_amount += amount
        
        message += f"📊 <b>Итого:</b> {total_amount:.2f} руб."
        
        # Разбиваем длинное сообщение на части
        chunks = split_text(message, MAX_MESSAGE_LENGTH)
        for part in chunks:
            await callback_query.message.answer(part, parse_mode=ParseMode.HTML)
            
    except SQLAlchemyError as e:
        logger.exception("DB error in process_earnings_year")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
    finally:
        session.close()
    await callback_query.answer()
