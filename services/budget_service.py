# services/budget_service.py
"""
Сервис для управления бюджетом турниров
"""

import logging
from datetime import datetime, date, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from sqlalchemy import func, and_
from sqlalchemy.orm import joinedload
import pytz

from database import SessionLocal
from models import Tournament, TournamentBudget, JudgePayment, User, Registration, RegistrationStatus

logger = logging.getLogger(__name__)

class BudgetService:
    """Сервис для управления бюджетом турниров"""
    
    def __init__(self, bot=None):
        self.bot = bot
        self.session = SessionLocal()
    
    def __del__(self):
        if hasattr(self, 'session'):
            self.session.close()
    
    async def send_budget_reminders(self) -> int:
        """Отправляет напоминания о бюджете за 12 часов до турнира"""
        reminders_sent = 0
        
        try:
            # Находим турниры, которые начинаются через 12 часов (используем MSK timezone)
            msk_tz = pytz.timezone('Europe/Moscow')
            target_time = datetime.now(msk_tz) + timedelta(hours=12)
            target_date = target_time.date()
            
            # Получаем турниры на завтра, для которых еще не установлен бюджет
            # ВАЖНО: Проверяем, что турнир существует (не был удален)
            tournaments = self.session.query(Tournament).filter(
                and_(
                    Tournament.date == target_date,
                    ~Tournament.tournament_id.in_(
                        self.session.query(TournamentBudget.tournament_id)
                    )
                )
            ).order_by(Tournament.name).all()
            
            # Фильтруем только существующие турниры (дополнительная проверка)
            valid_tournaments = []
            for tournament in tournaments:
                # Проверяем, что турнир действительно существует в БД
                check = self.session.query(Tournament).filter(
                    Tournament.tournament_id == tournament.tournament_id
                ).first()
                if check:
                    valid_tournaments.append(tournament)
                else:
                    logger.warning(f"Турнир {tournament.tournament_id} ({tournament.name}) не найден в БД, пропускаем напоминание")
            
            if valid_tournaments:
                # Если турниров несколько, отправляем групповое сообщение
                if len(valid_tournaments) > 1:
                    await self._send_group_budget_reminder(valid_tournaments)
                    reminders_sent = 1
                else:
                    # Если турнир один, отправляем обычное напоминание
                    await self._send_budget_reminder(valid_tournaments[0])
                    reminders_sent = 1
            
            logger.info(f"Отправлено {reminders_sent} напоминаний о бюджете для {len(valid_tournaments)} турниров")
            
        except Exception as e:
            logger.error(f"Ошибка при отправке напоминаний о бюджете: {e}")
        
        return reminders_sent
    
    async def _send_budget_reminder(self, tournament: Tournament):
        """Отправляет напоминание о бюджете конкретному турниру"""
        from keyboards import budget_reminder_keyboard
        
        message = (
            f"💰 <b>Напоминание о бюджете турнира</b>\n\n"
            f"🏆 <b>Турнир:</b> {tournament.name}\n"
            f"📅 <b>Дата:</b> {tournament.date.strftime('%d.%m.%Y')}\n"
            f"⏰ <b>Начало через:</b> 12 часов\n\n"
            f"Какая общая сумма на судейскую бригаду на <b>«{tournament.name}»</b>?"
        )
        
        if self.bot:
            # Используем конфигурацию вместо хардкода
            from config import ADMIN_IDS
            for admin_id in ADMIN_IDS:
                await self.bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    reply_markup=budget_reminder_keyboard(tournament.tournament_id),
                    parse_mode='HTML'
                )
    
    async def _send_group_budget_reminder(self, tournaments: List[Tournament]):
        """Отправляет групповое напоминание о бюджете для нескольких турниров"""
        from keyboards import group_budget_reminder_keyboard
        
        message = (
            f"💰 <b>Напоминание о бюджете турниров</b>\n\n"
            f"📅 <b>Дата:</b> {tournaments[0].date.strftime('%d.%m.%Y')}\n"
            f"⏰ <b>Начало через:</b> 12 часов\n"
            f"🏆 <b>Турниров:</b> {len(tournaments)}\n\n"
            f"<b>Список турниров:</b>\n"
        )
        
        for i, tournament in enumerate(tournaments, 1):
            message += f"{i}. {tournament.name}\n"
        
        message += f"\nВыберите турнир для установки бюджета:"
        
        if self.bot:
            # Используем конфигурацию вместо хардкода
            from config import ADMIN_IDS
            for admin_id in ADMIN_IDS:
                await self.bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    reply_markup=group_budget_reminder_keyboard(tournaments),
                    parse_mode='HTML'
                )
    
    async def set_tournament_budget(self, tournament_id: int, total_budget: float) -> bool:
        """Устанавливает бюджет для турнира"""
        try:
            # Проверяем, что турнир существует
            tournament = self.session.query(Tournament).filter(
                Tournament.tournament_id == tournament_id
            ).first()
            
            if not tournament:
                logger.error(f"Турнир с ID {tournament_id} не найден")
                return False
            
            # Создаем или обновляем запись о бюджете
            budget = self.session.query(TournamentBudget).filter(
                TournamentBudget.tournament_id == tournament_id
            ).first()
            
            if budget:
                budget.total_budget = total_budget
                budget.budget_set_date = datetime.utcnow()
            else:
                budget = TournamentBudget(
                    tournament_id=tournament_id,
                    total_budget=total_budget
                )
                self.session.add(budget)
            
            self.session.commit()
            
            # Пересчитываем прибыль админа
            await self._recalculate_admin_profit(tournament_id)
            
            logger.info(f"Бюджет для турнира {tournament_id} установлен: {total_budget} руб.")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при установке бюджета для турнира {tournament_id}: {e}")
            self.session.rollback()
            return False
    
    async def _recalculate_admin_profit(self, tournament_id: int):
        """Пересчитывает прибыль админа для турнира"""
        try:
            budget = self.session.query(TournamentBudget).filter(
                TournamentBudget.tournament_id == tournament_id
            ).first()
            
            if not budget:
                return
            
            # Считаем общую сумму выплат судьям
            total_judges_payment = self.session.query(func.sum(JudgePayment.amount)).filter(
                and_(
                    JudgePayment.tournament_id == tournament_id,
                    JudgePayment.is_paid == True,
                    JudgePayment.amount.isnot(None)
                )
            ).scalar() or 0
            
            # Обновляем данные
            budget.judges_payment = float(total_judges_payment)
            budget.admin_profit = float(budget.total_budget - total_judges_payment)
            
            self.session.commit()
            
        except Exception as e:
            logger.error(f"Ошибка при пересчете прибыли для турнира {tournament_id}: {e}")
            self.session.rollback()
    
    async def get_tournament_budget(self, tournament_id: int) -> Optional[Dict]:
        """Получает информацию о бюджете турнира"""
        try:
            budget = self.session.query(TournamentBudget).filter(
                TournamentBudget.tournament_id == tournament_id
            ).first()
            
            if not budget:
                return None
            
            return {
                'tournament_id': budget.tournament_id,
                'total_budget': budget.total_budget,
                'judges_payment': budget.judges_payment or 0,
                'admin_profit': budget.admin_profit or 0,
                'budget_set_date': budget.budget_set_date,
                'reminder_sent': budget.reminder_sent
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении бюджета турнира {tournament_id}: {e}")
            return None
    
    async def get_all_budgets(self) -> List[Dict]:
        """Получает информацию о всех бюджетах"""
        try:
            budgets = self.session.query(TournamentBudget).join(Tournament).order_by(
                Tournament.date.desc()
            ).all()
            
            result = []
            for budget in budgets:
                result.append({
                    'tournament_id': budget.tournament_id,
                    'tournament_name': budget.tournament.name,
                    'tournament_date': budget.tournament.date,
                    'total_budget': budget.total_budget,
                    'judges_payment': budget.judges_payment or 0,
                    'admin_profit': budget.admin_profit or 0,
                    'budget_set_date': budget.budget_set_date
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при получении всех бюджетов: {e}")
            return []
    
    async def get_admin_profit_summary(self) -> Dict:
        """Получает сводку по прибыли админа"""
        try:
            # Общая прибыль
            total_profit = self.session.query(func.sum(TournamentBudget.admin_profit)).filter(
                TournamentBudget.admin_profit.isnot(None)
            ).scalar() or 0
            
            # Прибыль за месяц
            month_start = date.today().replace(day=1)
            monthly_profit = self.session.query(func.sum(TournamentBudget.admin_profit)).join(
                Tournament
            ).filter(
                and_(
                    Tournament.date >= month_start,
                    TournamentBudget.admin_profit.isnot(None)
                )
            ).scalar() or 0
            
            # Прибыль за сезон
            current_season_start = self._get_current_season_start()
            seasonal_profit = self.session.query(func.sum(TournamentBudget.admin_profit)).join(
                Tournament
            ).filter(
                and_(
                    Tournament.date >= current_season_start,
                    TournamentBudget.admin_profit.isnot(None)
                )
            ).scalar() or 0
            
            # Количество турниров с прибылью
            tournaments_with_profit = self.session.query(TournamentBudget).filter(
                TournamentBudget.admin_profit.isnot(None)
            ).count()
            
            return {
                'total_profit': float(total_profit),
                'monthly_profit': float(monthly_profit),
                'seasonal_profit': float(seasonal_profit),
                'tournaments_count': tournaments_with_profit
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении сводки по прибыли: {e}")
            return {
                'total_profit': 0.0,
                'monthly_profit': 0.0,
                'seasonal_profit': 0.0,
                'tournaments_count': 0
            }
    
    async def update_judges_payment(self, tournament_id: int):
        """Обновляет выплаты судьям при изменении платежей"""
        await self._recalculate_admin_profit(tournament_id)
    
    def _get_current_season_start(self) -> date:
        """Получает дату начала текущего сезона"""
        current_date = date.today()
        if current_date.month >= 9:  # Сентябрь и позже
            return date(current_date.year, 9, 1)
        else:  # До сентября
            return date(current_date.year - 1, 9, 1)

# Глобальный экземпляр сервиса
_budget_service = None

def get_budget_service(bot=None) -> BudgetService:
    """Получает экземпляр сервиса бюджета"""
    global _budget_service
    if _budget_service is None or _budget_service.bot != bot:
        _budget_service = BudgetService(bot)
    return _budget_service
