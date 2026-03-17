from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    """
    Главное меню для пользователя (судьи).
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🏆 Записаться на турнир", callback_data='sign_up'),
        InlineKeyboardButton("🚫 Отменить запись", callback_data='cancel_registration'),
        InlineKeyboardButton("📋 Мои записи", callback_data='my_registrations'),
        InlineKeyboardButton("💰 Мой заработок", callback_data='my_earnings'),
        InlineKeyboardButton("⚙️ Изменить профиль", callback_data='edit_profile'),
        InlineKeyboardButton("🔙 Назад в главное меню", callback_data='back_to_main')
    )
    return keyboard

def admin_menu_keyboard():
    """
    Меню администратора.
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📊 Дашборд", callback_data='admin_dashboard'),
        InlineKeyboardButton("➕ Добавить турнир", callback_data='admin_add_tournament'),
        InlineKeyboardButton("👥 Просмотр судей", callback_data='admin_view_referees'),
        InlineKeyboardButton("📅 Просмотр турниров", callback_data='admin_view_tournaments'),
        InlineKeyboardButton("✏️ Изменить турнир", callback_data='admin_edit_tournament'),
        InlineKeyboardButton("🗑️ Удалить турнир", callback_data='admin_delete_tournament'),
        InlineKeyboardButton("📝 Рассмотреть заявки", callback_data='admin_review_registrations'),
        InlineKeyboardButton("🔍 Проверка записей", callback_data='admin_check_registrations'),
        InlineKeyboardButton("💰 Заработок судей", callback_data='admin_judge_earnings'),
        InlineKeyboardButton("✏️ Ручной ввод заработка", callback_data='admin_manual_payment'),
        InlineKeyboardButton("💼 Бюджеты турниров", callback_data='admin_budget_info'),
        InlineKeyboardButton("📈 Моя прибыль", callback_data='admin_profit_dashboard'),
        InlineKeyboardButton("📊 Экспорт в Excel", callback_data='admin_export_data'),
        InlineKeyboardButton("📢 Рассылка", callback_data='admin_sendall'),
        InlineKeyboardButton("🔙 Назад в админ-меню", callback_data='back_to_admin_main')
    )
    return keyboard

def cancel_keyboard(context_type: str = "user"):
    """
    Клавиатура отмены для разных контекстов
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    if context_type == "admin":
        keyboard.add(InlineKeyboardButton("❌ Отменить", callback_data='admin_menu'))
    else:
        keyboard.add(InlineKeyboardButton("❌ Отменить", callback_data='back_to_main'))
    return keyboard

def month_selection_keyboard(months: list, callback_prefix: str, back_callback: str = "back_to_main"):
    """
    Универсальная клавиатура выбора месяца
    """
    keyboard = InlineKeyboardMarkup(row_width=3)
    for month in months:
        keyboard.insert(InlineKeyboardButton(month, callback_data=f'{callback_prefix}_{month}'))
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data=back_callback))
    return keyboard

def confirmation_keyboard(confirm_callback: str, cancel_callback: str = "cancel_action"):
    """
    Клавиатура подтверждения
    """
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Да", callback_data=confirm_callback),
        InlineKeyboardButton("❌ Нет", callback_data=cancel_callback)
    )
    return keyboard

def payment_reminder_keyboard(payment_id: int):
    """
    Клавиатура для напоминания об оплате
    """
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Да, заплатил", callback_data=f'payment_yes_{payment_id}'),
        InlineKeyboardButton("❌ Нет, не заплатил", callback_data=f'payment_no_{payment_id}')
    )
    return keyboard

def earnings_menu_keyboard():
    """
    Меню заработка судьи
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📊 Заработок подробно", callback_data='earnings_detailed'),
        InlineKeyboardButton("📈 Краткий обзор", callback_data='earnings_summary'),
        InlineKeyboardButton("✏️ Исправить заработок", callback_data='correct_earnings'),
        InlineKeyboardButton("🔙 Назад в главное меню", callback_data='back_to_main')
    )
    return keyboard

def admin_earnings_menu_keyboard():
    """
    Меню заработка судей для админа
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📅 Заработок по месяцам", callback_data='admin_earnings_monthly'),
        InlineKeyboardButton("📆 Заработок за год", callback_data='admin_earnings_yearly'),
        InlineKeyboardButton("🎓 Заработок за сезон", callback_data='admin_earnings_seasonal'),
        InlineKeyboardButton("🔙 Назад в админ-меню", callback_data='back_to_admin_main')
    )
    return keyboard

def month_selection_earnings_keyboard(months: list):
    """
    Клавиатура выбора месяца для заработка
    """
    keyboard = InlineKeyboardMarkup(row_width=3)
    for month in months:
        keyboard.insert(InlineKeyboardButton(month, callback_data=f'earnings_month_{month}'))
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data='admin_judge_earnings'))
    return keyboard

def year_selection_earnings_keyboard(years: list):
    """
    Клавиатура выбора года для заработка
    """
    keyboard = InlineKeyboardMarkup(row_width=3)
    for year in years:
        keyboard.insert(InlineKeyboardButton(str(year), callback_data=f'earnings_year_{year}'))
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data='admin_judge_earnings'))
    return keyboard

def budget_reminder_keyboard(tournament_id: int):
    """
    Клавиатура для напоминания о бюджете турнира
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("💰 Установить бюджет", callback_data=f'set_budget_{tournament_id}'),
        InlineKeyboardButton("⏰ Напомнить позже", callback_data=f'remind_later_{tournament_id}'),
        InlineKeyboardButton("❌ Пропустить", callback_data=f'skip_budget_{tournament_id}')
    )
    return keyboard

def group_budget_reminder_keyboard(tournaments):
    """
    Клавиатура для выбора турнира из группы
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Добавляем кнопки для каждого турнира
    for i, tournament in enumerate(tournaments, 1):
        # Ограничиваем длину названия турнира
        tournament_name = tournament.name[:30] + "..." if len(tournament.name) > 30 else tournament.name
        keyboard.add(
            InlineKeyboardButton(
                f"🏆 {i}. {tournament_name}", 
                callback_data=f'set_budget_{tournament.tournament_id}'
            )
        )
    
    # Добавляем общие действия
    keyboard.add(
        InlineKeyboardButton("⏰ Напомнить позже", callback_data=f'remind_later_group_{tournaments[0].date.strftime("%Y-%m-%d")}'),
        InlineKeyboardButton("❌ Пропустить все", callback_data=f'skip_budget_group_{tournaments[0].date.strftime("%Y-%m-%d")}')
    )
    
    return keyboard
