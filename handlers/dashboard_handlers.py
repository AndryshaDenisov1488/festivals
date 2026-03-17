# handlers/dashboard_handlers.py
"""
Обработчики для дашборда админа
"""

import logging
from datetime import datetime
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode

from services.dashboard_service import get_dashboard_service
from utils.error_monitor import get_error_monitor

logger = logging.getLogger(__name__)

async def show_admin_dashboard(callback_query: types.CallbackQuery):
    """Показывает дашборд админа"""
    try:
        dashboard_service = get_dashboard_service()
        data = await dashboard_service.get_dashboard_data()
        
        if not data:
            await callback_query.message.answer("❌ Ошибка при загрузке данных дашборда")
            await callback_query.answer()
            return
        
        # Формируем сообщение дашборда
        message = _format_dashboard_message(data)
        
        # Создаем клавиатуру
        keyboard = _create_dashboard_keyboard()
        
        await callback_query.message.answer(
            message,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
        
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при показе дашборда: {e}")
        await callback_query.message.answer("❌ Произошла ошибка при загрузке дашборда")
        
        # Отправляем ошибку в мониторинг
        error_monitor = get_error_monitor()
        if error_monitor:
            await error_monitor.log_critical_error(e, "show_admin_dashboard", callback_query.from_user.id)
        
        await callback_query.answer()

def _format_dashboard_message(data: dict) -> str:
    """Форматирует сообщение дашборда"""
    
    # Заголовок
    message = "📊 <b>ДАШБОРД АДМИНА</b>\n"
    message += f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
    message += "═" * 40 + "\n\n"
    
    # Информация о сезоне
    season = data.get('season_info', {})
    message += f"🎓 <b>СЕЗОН {season.get('start', '—')} - {season.get('end', '—')}</b>\n"
    message += f"📈 Прогресс: {season.get('progress', 0)}% | До конца: {season.get('days_to_end', 0)} дней\n\n"
    
    # Судьи
    judges = data.get('judges', {})
    message += f"👥 <b>СУДЬИ:</b>\n"
    message += f"   • Всего: {judges.get('total', 0)}\n"
    message += f"   • Активных: {judges.get('active', 0)}\n"
    message += f"   • Новых в месяце: {judges.get('new_this_month', 0)}\n"
    if judges.get('most_active', {}).get('name') != 'Нет данных':
        message += f"   • Самый активный: {judges.get('most_active', {}).get('name', '—')} ({judges.get('most_active', {}).get('tournaments', 0)} турниров)\n"
    message += "\n"
    
    # Турниры
    tournaments = data.get('tournaments', {})
    message += f"🏆 <b>ТУРНИРЫ:</b>\n"
    message += f"   • В сезоне: {tournaments.get('total_season', 0)}\n"
    message += f"   • Прошло: {tournaments.get('past', 0)}\n"
    message += f"   • Запланировано: {tournaments.get('planned', 0)}\n"
    message += f"   • Ближайший: {tournaments.get('next', {}).get('name', '—')} ({tournaments.get('next', {}).get('date', '—')})\n"
    if tournaments.get('next', {}).get('days_left', 0) > 0:
        message += f"   • До ближайшего: {tournaments.get('next', {}).get('days_left', 0)} дней\n"
    message += f"   • Популярный день: {tournaments.get('popular_day', '—')}\n\n"
    
    # Заявки
    registrations = data.get('registrations', {})
    message += f"📝 <b>ЗАЯВКИ:</b>\n"
    message += f"   • Ожидают: {registrations.get('pending', 0)}\n"
    message += f"   • Утверждено сегодня: {registrations.get('approved_today', 0)}\n"
    message += f"   • Отклонено сегодня: {registrations.get('rejected_today', 0)}\n"
    message += f"   • За неделю: {registrations.get('this_week', 0)}\n\n"
    
    # Финансы
    finances = data.get('finances', {})
    message += f"💰 <b>ФИНАНСЫ:</b>\n"
    message += f"   • Выплачено: {finances.get('total_paid', 0):,.0f} руб.\n"
    message += f"   • К доплате: {finances.get('unpaid', 0):,.0f} руб.\n"
    message += f"   • Средний за турнир: {finances.get('avg_per_tournament', 0):,.0f} руб.\n"
    message += f"   • За месяц: {finances.get('monthly_payments', 0):,.0f} руб.\n\n"
    
    # Бюджеты
    budget = data.get('budget', {})
    if budget.get('tournaments_with_budget', 0) > 0:
        message += f"💼 <b>БЮДЖЕТЫ ТУРНИРОВ:</b>\n"
        message += f"   • Общий бюджет: {budget.get('total_budgets', 0):,.0f} руб.\n"
        message += f"   • Выплачено судьям: {budget.get('total_judges_payment', 0):,.0f} руб.\n"
        message += f"   • Ваша прибыль: {budget.get('total_admin_profit', 0):,.0f} руб.\n"
        message += f"   • Турниров с бюджетом: {budget.get('tournaments_with_budget', 0)}\n"
        message += f"   • Средняя рентабельность: {budget.get('avg_profitability', 0)}%\n\n"
    
    # Активность
    activity = data.get('activity', {})
    message += f"📈 <b>АКТИВНОСТЬ:</b>\n"
    message += f"   • Записей за неделю: {activity.get('registrations_week', 0)}\n"
    message += f"   • Записей за месяц: {activity.get('registrations_month', 0)}\n"
    message += f"   • Популярный день: {activity.get('popular_day', '—')}\n\n"
    
    # Топ судей
    top_judges = data.get('top_judges', [])
    if top_judges:
        message += f"🔥 <b>ТОП-3 СУДЕЙ ПО ЗАРАБОТКУ:</b>\n"
        for i, judge in enumerate(top_judges[:3], 1):
            message += f"   {i}. {judge.get('name', '—')} - {judge.get('amount', 0):,.0f} руб. ({judge.get('tournaments', 0)} турниров)\n"
        message += "\n"
    
    # Предупреждения
    alerts = data.get('alerts', [])
    if alerts:
        message += f"🚨 <b>УВЕДОМЛЕНИЯ:</b>\n"
        for alert in alerts:
            message += f"   {alert.get('message', '—')}\n"
        message += "\n"
    
    # Последняя активность
    recent_activity = data.get('recent_activity', [])
    if recent_activity:
        message += f"⏰ <b>ПОСЛЕДНЯЯ АКТИВНОСТЬ:</b>\n"
        for activity in recent_activity[:3]:
            message += f"   {activity.get('status', '❓')} {activity.get('judge', '—')} → {activity.get('tournament', '—')} ({activity.get('date', '—')}) {activity.get('time', '—')}\n"
    
    return message

def _create_dashboard_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для дашборда"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    # Основные действия
    keyboard.add(
        InlineKeyboardButton("🔄 Обновить", callback_data='admin_dashboard'),
        InlineKeyboardButton("📊 Детальная статистика", callback_data='admin_detailed_stats')
    )
    
    # Быстрые действия
    keyboard.add(
        InlineKeyboardButton("👥 Судьи", callback_data='admin_view_referees'),
        InlineKeyboardButton("🏆 Турниры", callback_data='admin_view_tournaments')
    )
    
    keyboard.add(
        InlineKeyboardButton("📝 Заявки", callback_data='admin_review_registrations'),
        InlineKeyboardButton("💰 Заработок", callback_data='admin_judge_earnings')
    )
    
    keyboard.add(
        InlineKeyboardButton("📤 Экспорт", callback_data='admin_export_data'),
        InlineKeyboardButton("🔙 Админ меню", callback_data='admin_menu')
    )
    
    return keyboard

async def show_detailed_stats(callback_query: types.CallbackQuery):
    """Показывает детальную статистику"""
    try:
        dashboard_service = get_dashboard_service()
        data = await dashboard_service.get_dashboard_data()
        
        if not data:
            await callback_query.message.answer("❌ Ошибка при загрузке детальной статистики")
            await callback_query.answer()
            return
        
        # Формируем детальную статистику
        message = _format_detailed_stats_message(data)
        
        # Создаем клавиатуру
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton("📊 Основной дашборд", callback_data='admin_dashboard'),
            InlineKeyboardButton("🔙 Админ меню", callback_data='admin_menu')
        )
        
        await callback_query.message.answer(
            message,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
        
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при показе детальной статистики: {e}")
        await callback_query.message.answer("❌ Произошла ошибка при загрузке детальной статистики")
        await callback_query.answer()

def _format_detailed_stats_message(data: dict) -> str:
    """Форматирует сообщение детальной статистики"""
    
    message = "📊 <b>ДЕТАЛЬНАЯ СТАТИСТИКА</b>\n"
    message += f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
    message += "═" * 50 + "\n\n"
    
    # Детальная статистика по судьям
    judges = data.get('judges', {})
    message += f"👥 <b>ДЕТАЛЬНАЯ СТАТИСТИКА СУДЕЙ:</b>\n"
    message += f"   • Всего зарегистрировано: {judges.get('total', 0)}\n"
    message += f"   • Активных в сезоне: {judges.get('active', 0)}\n"
    message += f"   • Новых в этом месяце: {judges.get('new_this_month', 0)}\n"
    message += f"   • Процент активности: {(judges.get('active', 0) / judges.get('total', 1)) * 100:.1f}%\n\n"
    
    # Детальная статистика по турнирам
    tournaments = data.get('tournaments', {})
    message += f"🏆 <b>ДЕТАЛЬНАЯ СТАТИСТИКА ТУРНИРОВ:</b>\n"
    message += f"   • Всего в сезоне: {tournaments.get('total_season', 0)}\n"
    message += f"   • Прошло: {tournaments.get('past', 0)}\n"
    message += f"   • Запланировано: {tournaments.get('planned', 0)}\n"
    message += f"   • Среднее в месяц: {tournaments.get('total_season', 0) / max(1, (datetime.now().month - 8) % 12):.1f}\n\n"
    
    # Детальная финансовая статистика
    finances = data.get('finances', {})
    message += f"💰 <b>ДЕТАЛЬНАЯ ФИНАНСОВАЯ СТАТИСТИКА:</b>\n"
    message += f"   • Общая сумма выплат: {finances.get('total_paid', 0):,.0f} руб.\n"
    message += f"   • К доплате: {finances.get('unpaid', 0):,.0f} руб.\n"
    message += f"   • Средний за турнир: {finances.get('avg_per_tournament', 0):,.0f} руб.\n"
    message += f"   • Выплаты за месяц: {finances.get('monthly_payments', 0):,.0f} руб.\n"
    message += f"   • Процент неоплаченных: {(finances.get('unpaid', 0) / max(1, finances.get('total_paid', 0) + finances.get('unpaid', 0))) * 100:.1f}%\n\n"
    
    # Топ судей (расширенный)
    top_judges = data.get('top_judges', [])
    if top_judges:
        message += f"🔥 <b>ТОП-5 СУДЕЙ ПО ЗАРАБОТКУ:</b>\n"
        for i, judge in enumerate(top_judges, 1):
            message += f"   {i}. {judge.get('name', '—')}\n"
            message += f"      💰 {judge.get('amount', 0):,.0f} руб. ({judge.get('tournaments', 0)} турниров)\n"
            message += f"      📊 Средний: {judge.get('avg_per_tournament', 0):,.0f} руб./турнир\n\n"
    
    return message
