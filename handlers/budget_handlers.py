# handlers/budget_handlers.py
"""
Обработчики для системы бюджетирования турниров
"""

import logging
from datetime import datetime
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode

from services.budget_service import get_budget_service
from utils.error_monitor import get_error_monitor

logger = logging.getLogger(__name__)

async def handle_budget_reminder(callback_query: types.CallbackQuery, state: FSMContext):
    """Обрабатывает напоминание о бюджете турнира"""
    try:
        data = callback_query.data
        
        if data.startswith('set_budget_'):
            # Пользователь хочет установить бюджет
            try:
                tournament_id = int(data.split('_')[-1])
            except (ValueError, IndexError) as e:
                logger.error(f"Invalid budget callback data: {data}, error: {e}")
                await callback_query.answer("❌ Ошибка в данных. Попробуйте позже.", show_alert=True)
                return
            
            # Получаем информацию о турнире
            from database import SessionLocal
            from models import Tournament
            session = SessionLocal()
            try:
                tournament = session.query(Tournament).filter(
                    Tournament.tournament_id == tournament_id
                ).first()
                
                if tournament:
                    await callback_query.message.edit_text(
                        f"💰 <b>Установка бюджета турнира</b>\n\n"
                        f"🏆 <b>Турнир:</b> {tournament.name}\n"
                        f"📅 <b>Дата:</b> {tournament.date.strftime('%d.%m.%Y')}\n\n"
                        f"Введите общую сумму на судейскую бригаду (только число):",
                        parse_mode=ParseMode.HTML
                    )
                else:
                    await callback_query.message.edit_text(
                        f"💰 <b>Установка бюджета турнира</b>\n\n"
                        f"Введите общую сумму на судейскую бригаду (только число):",
                        parse_mode=ParseMode.HTML
                    )
            finally:
                session.close()
            
            # Сохраняем ID турнира в состоянии
            await state.update_data(tournament_id=tournament_id)
            from states import BudgetInput
            await BudgetInput.waiting_for_amount.set()
            
        elif data.startswith('remind_later_'):
            if 'group_' in data:
                # Групповое напоминание позже
                date_str = data.split('group_')[-1]
                await callback_query.message.edit_text(
                    f"⏰ Напоминание отложено на 6 часов для всех турниров {date_str}.\n"
                    f"Вы получите новое напоминание позже.",
                    parse_mode=ParseMode.HTML
                )
            else:
                # Одиночное напоминание позже
                await callback_query.message.edit_text(
                    "⏰ Напоминание отложено на 6 часов.\n"
                    "Вы получите новое напоминание позже.",
                    parse_mode=ParseMode.HTML
                )
            
        elif data.startswith('skip_budget_'):
            if 'group_' in data:
                # Пропустить все турниры группы
                date_str = data.split('group_')[-1]
                await callback_query.message.edit_text(
                    f"❌ Установка бюджета пропущена для всех турниров {date_str}.\n"
                    f"Вы можете установить бюджет позже вручную.",
                    parse_mode=ParseMode.HTML
                )
            else:
                # Пропустить один турнир
                await callback_query.message.edit_text(
                    "❌ Установка бюджета пропущена.\n"
                    "Вы можете установить бюджет позже вручную.",
                    parse_mode=ParseMode.HTML
                )
        
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при обработке напоминания о бюджете: {e}")
        await callback_query.message.answer("❌ Произошла ошибка при обработке запроса")
        
        # Отправляем ошибку в мониторинг
        error_monitor = get_error_monitor()
        if error_monitor:
            await error_monitor.log_critical_error(e, "handle_budget_reminder", callback_query.from_user.id)
        
        await callback_query.answer()

async def process_budget_amount(message: types.Message, state: FSMContext):
    """Обрабатывает введенную сумму бюджета"""
    try:
        if not message.text:
            await message.answer("❌ Пожалуйста, отправьте текстовое сообщение.")
            return
            
        # Получаем сумму из сообщения
        try:
            budget_amount = float(message.text.replace(',', '.').strip())
        except ValueError:
            await message.answer("❌ Неверный формат суммы. Введите только число (например: 5000 или 5000.50):")
            return
        
        if budget_amount <= 0:
            await message.answer("❌ Сумма должна быть больше нуля. Введите корректную сумму:")
            return
        
        # Получаем ID турнира из состояния
        data = await state.get_data()
        tournament_id = data.get('tournament_id')
        
        if not tournament_id:
            await message.answer("❌ Ошибка: не найден ID турнира. Попробуйте снова.")
            await state.finish()
            return
        
        # Устанавливаем бюджет
        budget_service = get_budget_service(message.bot)
        success = await budget_service.set_tournament_budget(tournament_id, budget_amount)
        
        if success:
            await message.answer(
                f"✅ <b>Бюджет установлен!</b>\n\n"
                f"💰 Общая сумма: {budget_amount:,.0f} руб.\n"
                f"📊 Система будет отслеживать выплаты судьям и рассчитывать вашу прибыль.",
                parse_mode=ParseMode.HTML
            )
        else:
            await message.answer("❌ Ошибка при установке бюджета. Попробуйте позже.")
        
        await state.finish()
        
    except Exception as e:
        logger.error(f"Ошибка при обработке суммы бюджета: {e}")
        await message.answer("❌ Произошла ошибка при обработке суммы. Попробуйте снова.")
        
        # Отправляем ошибку в мониторинг
        error_monitor = get_error_monitor()
        if error_monitor:
            await error_monitor.log_critical_error(e, "process_budget_amount", message.from_user.id)
        
        await state.finish()

async def show_budget_info(callback_query: types.CallbackQuery):
    """Показывает информацию о бюджетах турниров"""
    try:
        budget_service = get_budget_service(callback_query.bot)
        budgets = await budget_service.get_all_budgets()
        
        if not budgets:
            await callback_query.message.answer(
                "📊 <b>Информация о бюджетах</b>\n\n"
                "❌ Нет установленных бюджетов турниров.",
                parse_mode=ParseMode.HTML
            )
            await callback_query.answer()
            return
        
        # Формируем сообщение с информацией о бюджетах
        message = "📊 <b>ИНФОРМАЦИЯ О БЮДЖЕТАХ ТУРНИРОВ</b>\n"
        message += f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        message += "═" * 50 + "\n\n"
        
        total_budget = 0
        total_judges_payment = 0
        total_admin_profit = 0
        
        for budget in budgets[:10]:  # Показываем последние 10
            message += f"🏆 <b>{budget['tournament_name']}</b>\n"
            message += f"📅 {budget['tournament_date'].strftime('%d.%m.%Y')}\n"
            message += f"💰 Бюджет: {budget['total_budget']:,.0f} руб.\n"
            message += f"👥 Судьям: {budget['judges_payment']:,.0f} руб.\n"
            message += f"💼 Ваша прибыль: {budget['admin_profit']:,.0f} руб.\n"
            message += f"📊 Рентабельность: {(budget['admin_profit'] / budget['total_budget'] * 100):.1f}%\n\n"
            
            total_budget += budget['total_budget']
            total_judges_payment += budget['judges_payment']
            total_admin_profit += budget['admin_profit']
        
        # Итоговая статистика
        message += "═" * 50 + "\n"
        message += f"📈 <b>ИТОГО:</b>\n"
        message += f"💰 Общий бюджет: {total_budget:,.0f} руб.\n"
        message += f"👥 Выплачено судьям: {total_judges_payment:,.0f} руб.\n"
        message += f"💼 Ваша общая прибыль: {total_admin_profit:,.0f} руб.\n"
        message += f"📊 Средняя рентабельность: {(total_admin_profit / total_budget * 100):.1f}%\n"
        
        # Создаем клавиатуру
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton("🔄 Обновить", callback_data='admin_budget_info'),
            InlineKeyboardButton("🔙 Админ меню", callback_data='admin_menu')
        )
        
        await callback_query.message.answer(
            message,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
        
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при показе информации о бюджетах: {e}")
        await callback_query.message.answer("❌ Произошла ошибка при загрузке информации о бюджетах")
        
        # Отправляем ошибку в мониторинг
        error_monitor = get_error_monitor()
        if error_monitor:
            await error_monitor.log_critical_error(e, "show_budget_info", callback_query.from_user.id)
        
        await callback_query.answer()

async def show_admin_profit_dashboard(callback_query: types.CallbackQuery):
    """Показывает дашборд прибыли админа"""
    try:
        budget_service = get_budget_service(callback_query.bot)
        profit_summary = await budget_service.get_admin_profit_summary()
        
        message = "💼 <b>ДАШБОРД ПРИБЫЛИ АДМИНА</b>\n"
        message += f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        message += "═" * 50 + "\n\n"
        
        message += f"💰 <b>ОБЩАЯ ПРИБЫЛЬ:</b> {profit_summary['total_profit']:,.0f} руб.\n"
        message += f"📅 <b>ЗА МЕСЯЦ:</b> {profit_summary['monthly_profit']:,.0f} руб.\n"
        message += f"🎓 <b>ЗА СЕЗОН:</b> {profit_summary['seasonal_profit']:,.0f} руб.\n"
        message += f"🏆 <b>ТУРНИРОВ С ПРИБЫЛЬЮ:</b> {profit_summary['tournaments_count']}\n\n"
        
        if profit_summary['tournaments_count'] > 0:
            avg_profit = profit_summary['total_profit'] / profit_summary['tournaments_count']
            message += f"📊 <b>СРЕДНЯЯ ПРИБЫЛЬ ЗА ТУРНИР:</b> {avg_profit:,.0f} руб.\n\n"
        
        # Получаем детальную информацию о последних турнирах
        budgets = await budget_service.get_all_budgets()
        if budgets:
            message += "🏆 <b>ПОСЛЕДНИЕ ТУРНИРЫ:</b>\n"
            for budget in budgets[:5]:
                profit_percent = (budget['admin_profit'] / budget['total_budget'] * 100) if budget['total_budget'] > 0 else 0
                message += f"• {budget['tournament_name']} ({budget['tournament_date'].strftime('%d.%m')}): {budget['admin_profit']:,.0f} руб. ({profit_percent:.1f}%)\n"
        
        # Создаем клавиатуру
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton("📊 Все бюджеты", callback_data='admin_budget_info'),
            InlineKeyboardButton("🔄 Обновить", callback_data='admin_profit_dashboard'),
            InlineKeyboardButton("🔙 Админ меню", callback_data='admin_menu')
        )
        
        await callback_query.message.answer(
            message,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
        
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при показе дашборда прибыли: {e}")
        await callback_query.message.answer("❌ Произошла ошибка при загрузке дашборда прибыли")
        
        # Отправляем ошибку в мониторинг
        error_monitor = get_error_monitor()
        if error_monitor:
            await error_monitor.log_critical_error(e, "show_admin_profit_dashboard", callback_query.from_user.id)
        
        await callback_query.answer()
