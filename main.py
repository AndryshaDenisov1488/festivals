import logging
import sys
import pytz
import datetime

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext

from config import BOT_TOKEN
from database import engine, SessionLocal
from models import Base, Registration, Tournament, RegistrationStatus, User
from utils.error_monitor import init_error_monitor, get_error_monitor
from utils.action_logger import init_action_logger
from utils.menu_manager import get_menu_manager
from utils.fsm_guard import get_fsm_guard

# === HANDLERS ===
from handlers.common_handlers import (
    cmd_start, process_first_name, process_last_name, process_function, process_category,
    process_back_to_main, process_cancel_payment_input,
)
from handlers.user_handlers import (
    process_sign_up, process_month, process_tournament, setup_main_menu_button_handlers,
    cmd_link_email, link_email_step, process_link_email_input, process_link_email_code,
    process_cancel_registration, process_cancel_reg_month, process_cancel_reg_id,
    process_confirm_cancel, process_cancel_action,
    my_registrations_step, process_my_registrations_month,
    edit_profile_step, process_edit_profile_first_name, process_edit_profile_last_name,
    process_edit_profile_function, process_edit_profile_category,
    # Система заработка
    process_my_earnings, process_earnings_detailed, process_earnings_summary,
    process_payment_yes, process_payment_no, process_payment_amount,
    process_correct_earnings, process_correct_earnings_tournament, process_correct_earnings_amount,
)
from handlers.admin_handlers import (
    # главное меню админа
    cmd_admin, admin_actions,
    # добавление турнира
    process_add_tournament_month, process_add_tournament_date, process_add_tournament_name,
    # редактирование турнира
    process_edit_tournament_month, process_edit_tournament_selection,
    process_edit_tournament_new_name,
    # просмотр турниров
    process_view_tournaments_month,
    # проверка записей
    process_check_registrations_month,
    # экспорт
    process_export_period, process_export_month, process_export_year,
    # рассмотрение заявок
    admin_review_tournaments_in_month, process_review_tournament,
    process_approve_registration, process_reject_registration,
    # календарь
    calendar_callbacks,
    # удаление турнира
    delete_tournament_step, process_delete_month, process_delete_tournament, process_delete_confirm,
    # рассылка
    process_sendall_message, admin_sendall_action,
    # заработок судей
    admin_judge_earnings_menu, admin_earnings_monthly, admin_earnings_yearly, admin_earnings_seasonal,
    process_earnings_month, process_earnings_year,
    # ручной ввод заработка
    admin_manual_payment, process_manual_payment_judge, process_manual_payment_tournament,
    process_manual_payment_amount,
)
from handlers.dashboard_handlers import (
    show_admin_dashboard, show_detailed_stats,
)
from handlers.budget_handlers import (
    handle_budget_reminder, process_budget_amount, show_budget_info, show_admin_profit_dashboard,
)

from states import (
    RegisterReferee, AddTournament, EditTournament, EditProfile,
    MyRegistrations, CheckRegistrations, SendAllMessages, DeleteTournament,
    PaymentAmount, BudgetInput, ManualPaymentInput, CorrectEarnings, LinkEmail,
)

# ========== Логирование ==========
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# ========== База ==========
Base.metadata.create_all(bind=engine)

# ========== Бот/Диспетчер ==========
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# ========== Планировщик ==========
from apscheduler.schedulers.asyncio import AsyncIOScheduler
scheduler = AsyncIOScheduler(timezone=pytz.timezone("Europe/Moscow"))

async def reminder_job():
    """
    Каждый день напоминаем об утверждённых на завтра турнирах.
    """
    session = SessionLocal()
    try:
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        tournaments_tomorrow = session.query(Tournament).filter(Tournament.date == tomorrow).all()

        for t in tournaments_tomorrow:
            regs_approved = session.query(Registration).filter(
                Registration.tournament_id == t.tournament_id,
                Registration.status == RegistrationStatus.APPROVED
            ).all()
            for reg in regs_approved:
                user = reg.user
                text = (
                    f"Добрый день!\n"
                    f"Напоминаю, что вы утверждены судить турнир <b>{t.date.strftime('%d.%m.%Y')} {t.name}</b> завтра.\n"
                    f"Если ваши планы поменялись, напишите Андрюше."
                )
                try:
                    await bot.send_message(user.user_id, text)
                    logger.info("[reminder_job] Sent reminder to user_id=%s", user.user_id)
                except Exception as e:
                    logger.error("[reminder_job] Could not send to user_id=%s: %s", user.user_id, e)
                if user.email:
                    try:
                        from api.email_service import send_tournament_reminder_email
                        send_tournament_reminder_email(
                            user.email,
                            t.name,
                            t.date.strftime('%d.%m.%Y')
                        )
                        logger.info("[reminder_job] Sent reminder email to %s", user.email)
                    except Exception as e:
                        logger.exception("[reminder_job] Email reminder failed for %s: %s", user.email, e)
    except Exception as e:
        logger.exception("[reminder_job] Unexpected error")
        # Отправляем критическую ошибку в канал мониторинга
        error_monitor = get_error_monitor()
        if error_monitor:
            await error_monitor.log_critical_error(e, "reminder_job")
    finally:
        session.close()

async def payment_reminder_job():
    """
    Проверяем, нужно ли отправить напоминания об оплате (в 18:00 в день турнира и каждые 6 часов).
    """
    try:
        from services.payment_system import get_payment_system
        payment_system = get_payment_system(bot)
        
        # Отправляем напоминания судьям
        reminders_sent = await payment_system.send_payment_reminders()
        if reminders_sent > 0:
            logger.info(f"[payment_reminder_job] Sent {reminders_sent} payment reminders")
        
        # Отправляем напоминания админу
        admin_reminders_sent = await payment_system.send_admin_reminders()
        if admin_reminders_sent > 0:
            logger.info(f"[payment_reminder_job] Sent {admin_reminders_sent} admin reminders")
            
    except Exception as e:
        logger.exception("[payment_reminder_job] Unexpected error")
        # Отправляем критическую ошибку в канал мониторинга
        error_monitor = get_error_monitor()
        if error_monitor:
            await error_monitor.log_critical_error(e, "payment_reminder_job")

async def budget_reminder_job():
    """
    Каждые 12 часов проверяем, нужно ли отправить напоминания о бюджете (за 12 часов до турнира).
    """
    try:
        from services.budget_service import get_budget_service
        budget_service = get_budget_service(bot)
        reminders_sent = await budget_service.send_budget_reminders()
        if reminders_sent > 0:
            logger.info(f"[budget_reminder_job] Sent {reminders_sent} budget reminders")
    except Exception as e:
        logger.exception("[budget_reminder_job] Unexpected error")
        # Отправляем критическую ошибку в канал мониторинга
        error_monitor = get_error_monitor()
        if error_monitor:
            await error_monitor.log_critical_error(e, "budget_reminder_job")

async def on_startup(_):
    # Инициализация мониторинга ошибок и логирования действий
    init_error_monitor(bot)
    init_action_logger(bot)
    logger.info("Error monitoring and action logging initialized")
    
    # Запуск FSM Guard для автоматического завершения сессий
    fsm_guard = get_fsm_guard()
    await fsm_guard.start_cleanup_task(bot)
    logger.info("FSM Guard started")
    
    # Очистка старых задач планировщика
    scheduler.remove_all_jobs()
    
    # запуск ежедневной джобы в 00:00 Мск
    scheduler.add_job(reminder_job, trigger="cron", hour=0, minute=0,
                      id="reminder_job", replace_existing=True)
    
    # запуск джобы для напоминаний об оплате в 18:00 в день турнира и каждые 6 часов
    scheduler.add_job(payment_reminder_job, trigger="cron", hour=18, minute=0,
                      id="payment_reminder_job_18", replace_existing=True)
    scheduler.add_job(payment_reminder_job, trigger="cron", hour=0, minute=0,
                      id="payment_reminder_job_00", replace_existing=True)
    scheduler.add_job(payment_reminder_job, trigger="cron", hour=6, minute=0,
                      id="payment_reminder_job_06", replace_existing=True)
    scheduler.add_job(payment_reminder_job, trigger="cron", hour=12, minute=0,
                      id="payment_reminder_job_12", replace_existing=True)
    
    # запуск джобы для напоминаний о бюджете каждые 12 часов (12:00 и 00:00 Мск)
    scheduler.add_job(budget_reminder_job, trigger="cron", hour=12, minute=0,
                      id="budget_reminder_job_12", replace_existing=True)
    scheduler.add_job(budget_reminder_job, trigger="cron", hour=0, minute=0,
                      id="budget_reminder_job_00", replace_existing=True)
    
    scheduler.start()
    logger.info("Scheduler started")

async def on_shutdown(_):
    try:
        # Останавливаем FSM Guard
        fsm_guard = get_fsm_guard()
        await fsm_guard.stop_cleanup_task()
        
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
    except Exception:
        logger.exception("Scheduler shutdown error")

# ========== Регистрация хендлеров ==========
logger.info("Registering handlers...")

# /start + регистрация судьи (message-handlers)
dp.register_message_handler(cmd_start, commands=["start"], state="*")
dp.register_message_handler(cmd_link_email, commands=["link_email"], state="*")
dp.register_message_handler(process_first_name, state=RegisterReferee.waiting_for_first_name)
dp.register_message_handler(process_last_name, state=RegisterReferee.waiting_for_last_name)
dp.register_message_handler(process_function, state=RegisterReferee.waiting_for_function)
dp.register_message_handler(process_category, state=RegisterReferee.waiting_for_category)

# Календарь
dp.register_callback_query_handler(calendar_callbacks, Text(startswith="cal_"), state="*")

# Главное меню (кнопка «Назад»)
dp.register_callback_query_handler(process_back_to_main, Text(equals="back_to_main"), state="*")

# Отмена ввода суммы оплаты
dp.register_callback_query_handler(process_cancel_payment_input, Text(equals="cancel_payment_input"), state="*")

# Кнопка «Вызвать главное меню» (ReplyButton)
setup_main_menu_button_handlers(dp)

# Пользовательские экраны (state="*" чтобы работало при любом FSM состоянии)
dp.register_callback_query_handler(process_sign_up, Text(equals="sign_up"), state="*")
dp.register_callback_query_handler(process_month, lambda c: c.data and c.data.startswith("month_"), state="*")
dp.register_callback_query_handler(process_tournament, lambda c: c.data and c.data.startswith("tournament_"), state="*")

dp.register_callback_query_handler(process_cancel_registration, Text(equals="cancel_registration"), state="*")
dp.register_callback_query_handler(process_cancel_reg_month, lambda c: c.data and c.data.startswith("cancel_reg_month_"), state="*")
dp.register_callback_query_handler(process_cancel_reg_id, lambda c: c.data and c.data.startswith("cancel_reg_id_"), state="*")
dp.register_callback_query_handler(process_confirm_cancel, lambda c: c.data and c.data.startswith("confirm_cancel_"), state="*")
dp.register_callback_query_handler(process_cancel_action, Text(equals="cancel_action"), state="*")

dp.register_callback_query_handler(my_registrations_step, Text(equals="my_registrations"), state="*")
dp.register_callback_query_handler(
    process_my_registrations_month,
    lambda c: c.data and c.data.startswith("my_registrations_month_"),
    state=MyRegistrations.waiting_for_month,
)

# Редактирование профиля
dp.register_callback_query_handler(edit_profile_step, Text(equals="edit_profile"), state="*")
dp.register_callback_query_handler(link_email_step, Text(equals="link_email"), state="*")
dp.register_message_handler(process_link_email_input, state=LinkEmail.waiting_for_email)
dp.register_message_handler(process_link_email_code, state=LinkEmail.waiting_for_code)
dp.register_message_handler(process_edit_profile_first_name, state=EditProfile.waiting_for_first_name)
dp.register_message_handler(process_edit_profile_last_name, state=EditProfile.waiting_for_last_name)
dp.register_message_handler(process_edit_profile_function, state=EditProfile.waiting_for_function)
dp.register_message_handler(process_edit_profile_category, state=EditProfile.waiting_for_category)

# Система заработка
# Регистрируем с state="*" чтобы обрабатывать даже когда пользователь в PaymentAmount
dp.register_callback_query_handler(process_my_earnings, Text(equals="my_earnings"), state="*")
dp.register_callback_query_handler(process_earnings_detailed, Text(equals="earnings_detailed"), state="*")
dp.register_callback_query_handler(process_earnings_summary, Text(equals="earnings_summary"), state="*")
dp.register_callback_query_handler(process_payment_yes, lambda c: c.data and c.data.startswith("payment_yes_"), state="*")
dp.register_callback_query_handler(process_payment_no, lambda c: c.data and c.data.startswith("payment_no_"), state="*")
dp.register_message_handler(process_payment_amount, state=PaymentAmount.waiting_for_amount)

# Исправление заработка судьей
dp.register_callback_query_handler(process_correct_earnings, Text(equals="correct_earnings"), state="*")
dp.register_callback_query_handler(process_correct_earnings_tournament, lambda c: c.data and c.data.startswith("correct_earnings_tournament_"), state="*")
dp.register_message_handler(process_correct_earnings_amount, state=CorrectEarnings.waiting_for_amount)

# Админка
dp.register_message_handler(cmd_admin, commands=["admin"], state="*")

# Админские команды - обрабатываются через admin_actions (state="*" чтобы работало при любом FSM состоянии)
dp.register_callback_query_handler(admin_actions, Text(equals="admin_add_tournament"), state="*")
dp.register_callback_query_handler(admin_actions, Text(equals="admin_view_referees"), state="*")
dp.register_callback_query_handler(admin_actions, Text(equals="admin_view_tournaments"), state="*")
dp.register_callback_query_handler(admin_actions, Text(equals="admin_edit_tournament"), state="*")
dp.register_callback_query_handler(admin_actions, Text(equals="admin_check_registrations"), state="*")
dp.register_callback_query_handler(admin_actions, Text(equals="admin_export_data"), state="*")
dp.register_callback_query_handler(admin_actions, Text(equals="admin_sendall"), state="*")
dp.register_callback_query_handler(admin_actions, Text(equals="admin_review_registrations"), state="*")
dp.register_callback_query_handler(admin_actions, Text(equals="admin_delete_tournament"), state="*")

# КНОПКА «Назад в админ-меню» (универсальная)
from keyboards import admin_menu_keyboard
async def _go_admin_menu(cb: types.CallbackQuery, state: FSMContext):
    from utils.menu_manager import get_menu_manager
    menu_manager = get_menu_manager()
    await menu_manager.handle_back_button(cb, state)
dp.register_callback_query_handler(_go_admin_menu, 
    lambda c: c.data in ["admin_menu", "back_to_admin_main"], state="*")

# Добавление турнира
dp.register_callback_query_handler(
    process_add_tournament_month,
    lambda c: c.data and c.data.startswith("add_tournament_month_"),
    state=AddTournament.waiting_for_month,
)
dp.register_message_handler(process_add_tournament_date, state=AddTournament.waiting_for_date)
dp.register_message_handler(process_add_tournament_name, state=AddTournament.waiting_for_name)

# Редактирование турнира
dp.register_callback_query_handler(
    process_edit_tournament_month,
    lambda c: c.data and c.data.startswith("edit_tournament_month_"),
    state=EditTournament.waiting_for_month,
)
dp.register_callback_query_handler(
    process_edit_tournament_selection,
    lambda c: c.data and c.data.startswith("edit_tournament_"),
    state=EditTournament.waiting_for_tournament_selection,
)
# Удален - теперь используется календарь
dp.register_message_handler(process_edit_tournament_new_name, state=EditTournament.waiting_for_new_name)

# Просмотр турниров
dp.register_callback_query_handler(
    process_view_tournaments_month,
    lambda c: c.data and c.data.startswith("view_tournaments_month_"),
    state="*",
)

# Проверка записей
dp.register_callback_query_handler(
    process_check_registrations_month,
    lambda c: c.data and c.data.startswith("check_registrations_month_"),
    state=CheckRegistrations.waiting_for_month,
)

# Экспорт
dp.register_callback_query_handler(process_export_period, lambda c: c.data and c.data.startswith("export_period_"), state="*")
dp.register_callback_query_handler(process_export_month,  lambda c: c.data and c.data.startswith("export_month_"), state="*")
dp.register_callback_query_handler(process_export_year,   lambda c: c.data and c.data.startswith("export_year_"), state="*")

# Рассмотрение заявок
dp.register_callback_query_handler(admin_review_tournaments_in_month, lambda c: c.data and c.data.startswith("review_month_"), state="*")
dp.register_callback_query_handler(process_review_tournament,         lambda c: c.data and c.data.startswith("review_tournament_"), state="*")
dp.register_callback_query_handler(process_approve_registration,      lambda c: c.data and c.data.startswith("approve_"), state="*")
dp.register_callback_query_handler(process_reject_registration,      lambda c: c.data and c.data.startswith("reject_"), state="*")

# Удаление турнира - обрабатывается через admin_actions
# dp.register_callback_query_handler(delete_tournament_step, lambda c: c.data == "admin_delete_tournament")
dp.register_callback_query_handler(
    process_delete_month, lambda c: c.data and c.data.startswith("delete_month_"), state=DeleteTournament.waiting_for_month
)
dp.register_callback_query_handler(
    process_delete_tournament,
    lambda c: c.data and c.data.startswith("delete_tournament_"),
    state=DeleteTournament.waiting_for_tournament_selection,
)
dp.register_callback_query_handler(
    process_delete_confirm,
    lambda c: c.data and c.data.startswith("delete_confirm_"),
    state=DeleteTournament.waiting_for_confirmation,
)

# Рассылка
dp.register_message_handler(process_sendall_message, state=SendAllMessages.waiting_for_message)

# Заработок судей (админ)
dp.register_callback_query_handler(admin_judge_earnings_menu, Text(equals="admin_judge_earnings"), state="*")
dp.register_callback_query_handler(admin_earnings_monthly, Text(equals="admin_earnings_monthly"), state="*")
dp.register_callback_query_handler(admin_earnings_yearly, Text(equals="admin_earnings_yearly"), state="*")
dp.register_callback_query_handler(admin_earnings_seasonal, Text(equals="admin_earnings_seasonal"), state="*")
dp.register_callback_query_handler(process_earnings_month, lambda c: c.data and c.data.startswith("earnings_month_"), state="*")
dp.register_callback_query_handler(process_earnings_year, lambda c: c.data and c.data.startswith("earnings_year_"), state="*")

# Ручной ввод заработка (админ)
dp.register_callback_query_handler(admin_manual_payment, Text(equals="admin_manual_payment"), state="*")
dp.register_callback_query_handler(process_manual_payment_judge, lambda c: c.data and c.data.startswith("manual_payment_judge_"), state="*")
dp.register_callback_query_handler(process_manual_payment_tournament, lambda c: c.data and c.data.startswith("manual_payment_tournament_"), state=ManualPaymentInput.waiting_for_tournament_selection)
dp.register_message_handler(process_manual_payment_amount, state=ManualPaymentInput.waiting_for_amount)

# Дашборд админа
dp.register_callback_query_handler(show_admin_dashboard, Text(equals="admin_dashboard"), state="*")
dp.register_callback_query_handler(show_detailed_stats, Text(equals="admin_detailed_stats"), state="*")

# Бюджетирование турниров
dp.register_callback_query_handler(handle_budget_reminder, lambda c: c.data and (c.data.startswith("set_budget_") or c.data.startswith("remind_later_") or c.data.startswith("skip_budget_")), state="*")
dp.register_message_handler(process_budget_amount, state=BudgetInput.waiting_for_amount)
dp.register_callback_query_handler(show_budget_info, Text(equals="admin_budget_info"), state="*")
dp.register_callback_query_handler(show_admin_profit_dashboard, Text(equals="admin_profit_dashboard"), state="*")

# Обработчик для выхода из состояния PaymentAmount при нажатии других кнопок
async def _handle_callback_in_payment_state(cb: types.CallbackQuery, state: FSMContext):
    """Обрабатывает callback-запросы во время состояния PaymentAmount"""
    current_state = await state.get_state()
    if current_state and current_state.startswith("PaymentAmount"):
        # Пользователь в состоянии ожидания ввода суммы оплаты
        # Завершаем состояние и позволяем обработать callback нормально
        from utils.fsm_guard import get_fsm_guard
        fsm_guard = get_fsm_guard()
        fsm_guard.end_session(cb.from_user.id)
        await state.finish()
        logger.info(f"Завершено состояние PaymentAmount для user_id={cb.from_user.id} при нажатии кнопки {cb.data}")

# ПОСЛЕДНИЙ — безопасный «дебаг»-логгер на непойманные колбэки
async def _debug_unhandled_cb(cb: types.CallbackQuery, state: FSMContext):
    # Сначала проверяем, не нужно ли выйти из PaymentAmount
    await _handle_callback_in_payment_state(cb, state)
    
    logging.getLogger("debug.cb").warning("UNHANDLED CALLBACK: %r (state=%s)", cb.data, await state.get_state())
    try:
        await cb.answer()
    except Exception as e:
        logging.getLogger("debug.cb").error("Failed to answer unhandled callback: %s", e)
dp.register_callback_query_handler(_debug_unhandled_cb, lambda c: True)

if __name__ == "__main__":
    logger.info("Запуск бота...")
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)
