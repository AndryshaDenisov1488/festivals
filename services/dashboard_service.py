# services/dashboard_service.py
"""
Сервис для создания дашборда админа
Собирает и обрабатывает данные для отображения статистики
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple, Any
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import joinedload

from database import SessionLocal
from models import User, Tournament, Registration, RegistrationStatus, JudgePayment

logger = logging.getLogger(__name__)

class DashboardService:
    """Сервис для создания дашборда админа"""
    
    def __init__(self):
        self.session = SessionLocal()
    
    def __del__(self):
        if hasattr(self, 'session'):
            self.session.close()
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Получает все данные для дашборда"""
        try:
            dashboard_data = {
                'judges': await self._get_judges_stats(),
                'tournaments': await self._get_tournaments_stats(),
                'registrations': await self._get_registrations_stats(),
                'finances': await self._get_finances_stats(),
                'activity': await self._get_activity_stats(),
                'top_judges': await self._get_top_judges(),
                'recent_activity': await self._get_recent_activity(),
                'season_info': await self._get_season_info(),
                'budget': await self._get_budget_stats(),
                'alerts': await self._get_alerts()
            }
            return dashboard_data
        except Exception as e:
            logger.error(f"Ошибка при получении данных дашборда: {e}")
            return {}
    
    async def _get_judges_stats(self) -> Dict[str, Any]:
        """Статистика по судьям"""
        try:
            total_judges = self.session.query(User).count()
            
            # Активные судьи (с записями в текущем сезоне)
            current_season_start = self._get_current_season_start()
            active_judges = self.session.query(User).join(Registration).join(Tournament).filter(
                Tournament.date >= current_season_start
            ).distinct().count()
            
            # Новые судьи в этом месяце
            month_start = date.today().replace(day=1)
            new_judges_this_month = self.session.query(User).filter(
                func.date(User.created_at) >= month_start
            ).count()
            
            # Судьи с наибольшим количеством турниров
            most_active_judge = self.session.query(
                User.first_name,
                User.last_name,
                func.count(Registration.registration_id).label('tournaments_count')
            ).join(Registration).join(Tournament).filter(
                Tournament.date >= current_season_start,
                Registration.status == RegistrationStatus.APPROVED
            ).group_by(User.user_id).order_by(
                func.count(Registration.registration_id).desc()
            ).first()
            
            return {
                'total': total_judges,
                'active': active_judges,
                'new_this_month': new_judges_this_month,
                'most_active': {
                    'name': f"{most_active_judge[0]} {most_active_judge[1]}" if most_active_judge else "Нет данных",
                    'tournaments': most_active_judge[2] if most_active_judge else 0
                }
            }
        except Exception as e:
            logger.error(f"Ошибка при получении статистики судей: {e}")
            return {'total': 0, 'active': 0, 'new_this_month': 0, 'most_active': {'name': 'Ошибка', 'tournaments': 0}}
    
    async def _get_tournaments_stats(self) -> Dict[str, Any]:
        """Статистика по турнирам"""
        try:
            current_season_start = self._get_current_season_start()
            
            # Все турниры в сезоне
            total_tournaments = self.session.query(Tournament).filter(
                Tournament.date >= current_season_start
            ).count()
            
            # Прошедшие турниры
            past_tournaments = self.session.query(Tournament).filter(
                and_(
                    Tournament.date >= current_season_start,
                    Tournament.date < date.today()
                )
            ).count()
            
            # Запланированные турниры
            planned_tournaments = self.session.query(Tournament).filter(
                Tournament.date >= date.today()
            ).count()
            
            # Ближайший турнир
            next_tournament = self.session.query(Tournament).filter(
                Tournament.date >= date.today()
            ).order_by(Tournament.date).first()
            
            # Популярный день недели
            popular_day = self.session.query(
                func.strftime('%w', Tournament.date).label('weekday'),
                func.count(Tournament.tournament_id).label('count')
            ).filter(
                Tournament.date >= current_season_start
            ).group_by('weekday').order_by(
                func.count(Tournament.tournament_id).desc()
            ).first()
            
            weekday_names = ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']
            popular_day_name = weekday_names[int(popular_day[0])] if popular_day else "Нет данных"
            
            return {
                'total_season': total_tournaments,
                'past': past_tournaments,
                'planned': planned_tournaments,
                'next': {
                    'name': next_tournament.name if next_tournament else "Нет запланированных",
                    'date': next_tournament.date.strftime('%d.%m.%Y') if next_tournament else "—",
                    'days_left': (next_tournament.date - date.today()).days if next_tournament else 0
                },
                'popular_day': popular_day_name
            }
        except Exception as e:
            logger.error(f"Ошибка при получении статистики турниров: {e}")
            return {'total_season': 0, 'past': 0, 'planned': 0, 'next': {'name': 'Ошибка', 'date': '—', 'days_left': 0}, 'popular_day': 'Ошибка'}
    
    async def _get_registrations_stats(self) -> Dict[str, Any]:
        """Статистика по заявкам"""
        try:
            # Ожидают рассмотрения
            pending = self.session.query(Registration).filter(
                Registration.status == RegistrationStatus.PENDING
            ).count()
            
            # Утверждено сегодня
            today = date.today()
            approved_today = self.session.query(Registration).join(Tournament).filter(
                and_(
                    Registration.status == RegistrationStatus.APPROVED,
                    func.date(Registration.updated_at) == today
                )
            ).count()
            
            # Отклонено сегодня
            rejected_today = self.session.query(Registration).join(Tournament).filter(
                and_(
                    Registration.status == RegistrationStatus.REJECTED,
                    func.date(Registration.updated_at) == today
                )
            ).count()
            
            # Заявки за неделю
            week_ago = date.today() - timedelta(days=7)
            registrations_this_week = self.session.query(Registration).join(Tournament).filter(
                Tournament.date >= week_ago
            ).count()
            
            return {
                'pending': pending,
                'approved_today': approved_today,
                'rejected_today': rejected_today,
                'this_week': registrations_this_week
            }
        except Exception as e:
            logger.error(f"Ошибка при получении статистики заявок: {e}")
            return {'pending': 0, 'approved_today': 0, 'rejected_today': 0, 'this_week': 0}
    
    async def _get_finances_stats(self) -> Dict[str, Any]:
        """Статистика по финансам"""
        try:
            # Выплачено судьям
            total_paid = self.session.query(func.sum(JudgePayment.amount)).filter(
                JudgePayment.is_paid == True,
                JudgePayment.amount.isnot(None)
            ).scalar() or 0
            
            # К доплате (неоплаченные)
            unpaid_amount = self.session.query(func.sum(JudgePayment.amount)).filter(
                JudgePayment.is_paid == False,
                JudgePayment.amount.isnot(None)
            ).scalar() or 0
            
            # Средний заработок за турнир
            avg_earnings = self.session.query(func.avg(JudgePayment.amount)).filter(
                JudgePayment.is_paid == True,
                JudgePayment.amount.isnot(None)
            ).scalar() or 0
            
            # Выплаты за месяц
            month_start = date.today().replace(day=1)
            monthly_payments = self.session.query(func.sum(JudgePayment.amount)).filter(
                and_(
                    JudgePayment.is_paid == True,
                    JudgePayment.payment_date >= month_start,
                    JudgePayment.amount.isnot(None)
                )
            ).scalar() or 0
            
            return {
                'total_paid': float(total_paid),
                'unpaid': float(unpaid_amount),
                'avg_per_tournament': float(avg_earnings),
                'monthly_payments': float(monthly_payments)
            }
        except Exception as e:
            logger.error(f"Ошибка при получении финансовой статистики: {e}")
            return {'total_paid': 0.0, 'unpaid': 0.0, 'avg_per_tournament': 0.0, 'monthly_payments': 0.0}
    
    async def _get_activity_stats(self) -> Dict[str, Any]:
        """Статистика активности"""
        try:
            # Записи за неделю
            week_ago = date.today() - timedelta(days=7)
            registrations_week = self.session.query(Registration).join(Tournament).filter(
                Tournament.date >= week_ago
            ).count()
            
            # Записи за месяц
            month_start = date.today().replace(day=1)
            registrations_month = self.session.query(Registration).join(Tournament).filter(
                Tournament.date >= month_start
            ).count()
            
            # Самый активный день недели
            popular_day = self.session.query(
                func.strftime('%w', Tournament.date).label('weekday'),
                func.count(Registration.registration_id).label('count')
            ).join(Registration).filter(
                Tournament.date >= month_start
            ).group_by('weekday').order_by(
                func.count(Registration.registration_id).desc()
            ).first()
            
            weekday_names = ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']
            popular_day_name = weekday_names[int(popular_day[0])] if popular_day else "Нет данных"
            
            return {
                'registrations_week': registrations_week,
                'registrations_month': registrations_month,
                'popular_day': popular_day_name
            }
        except Exception as e:
            logger.error(f"Ошибка при получении статистики активности: {e}")
            return {'registrations_week': 0, 'registrations_month': 0, 'popular_day': 'Ошибка'}
    
    async def _get_top_judges(self) -> List[Dict[str, Any]]:
        """Топ судей по заработку"""
        try:
            top_judges = self.session.query(
                User.first_name,
                User.last_name,
                func.sum(JudgePayment.amount).label('total_amount'),
                func.count(JudgePayment.payment_id).label('tournaments_count')
            ).join(JudgePayment).filter(
                JudgePayment.is_paid == True,
                JudgePayment.amount.isnot(None)
            ).group_by(User.user_id).order_by(
                func.sum(JudgePayment.amount).desc()
            ).limit(5).all()
            
            return [
                {
                    'name': f"{judge[0]} {judge[1]}",
                    'amount': float(judge[2]),
                    'tournaments': judge[3],
                    'avg_per_tournament': float(judge[2]) / judge[3] if judge[3] > 0 else 0
                }
                for judge in top_judges
            ]
        except Exception as e:
            logger.error(f"Ошибка при получении топ судей: {e}")
            return []
    
    async def _get_recent_activity(self) -> List[Dict[str, Any]]:
        """Последняя активность"""
        try:
            # Последние 5 записей на турниры
            recent_registrations = self.session.query(
                User.first_name,
                User.last_name,
                Tournament.name,
                Tournament.date,
                Registration.status,
                Registration.created_at
            ).join(Registration).join(Tournament).order_by(
                Registration.created_at.desc()
            ).limit(5).all()
            
            activities = []
            for reg in recent_registrations:
                status_emoji = {
                    RegistrationStatus.PENDING: '⏳',
                    RegistrationStatus.APPROVED: '✅',
                    RegistrationStatus.REJECTED: '❌'
                }.get(reg[4], '❓')
                
                activities.append({
                    'type': 'registration',
                    'judge': f"{reg[0]} {reg[1]}",
                    'tournament': reg[2],
                    'date': reg[3].strftime('%d.%m'),
                    'status': status_emoji,
                    'time': reg[5].strftime('%H:%M')
                })
            
            return activities
        except Exception as e:
            logger.error(f"Ошибка при получении последней активности: {e}")
            return []
    
    async def _get_season_info(self) -> Dict[str, Any]:
        """Информация о сезоне"""
        try:
            current_season_start = self._get_current_season_start()
            current_season_end = self._get_current_season_end()
            
            # Дней до конца сезона
            days_to_end = (current_season_end - date.today()).days
            
            # Прогресс сезона
            total_days = (current_season_end - current_season_start).days
            passed_days = (date.today() - current_season_start).days
            progress = min(100, max(0, (passed_days / total_days) * 100)) if total_days > 0 else 0
            
            return {
                'start': current_season_start.strftime('%d.%m.%Y'),
                'end': current_season_end.strftime('%d.%m.%Y'),
                'days_to_end': days_to_end,
                'progress': round(progress, 1)
            }
        except Exception as e:
            logger.error(f"Ошибка при получении информации о сезоне: {e}")
            return {'start': '—', 'end': '—', 'days_to_end': 0, 'progress': 0}
    
    async def _get_alerts(self) -> List[Dict[str, str]]:
        """Предупреждения и уведомления"""
        alerts = []
        
        try:
            # Неоплаченные турниры
            unpaid_count = self.session.query(JudgePayment).filter(
                JudgePayment.is_paid == False
            ).count()
            
            if unpaid_count > 0:
                alerts.append({
                    'type': 'warning',
                    'message': f'⚠️ {unpaid_count} неоплаченных турниров',
                    'action': 'admin_judge_earnings'
                })
            
            # Необработанные заявки
            pending_count = self.session.query(Registration).filter(
                Registration.status == RegistrationStatus.PENDING
            ).count()
            
            if pending_count > 0:
                alerts.append({
                    'type': 'info',
                    'message': f'📝 {pending_count} заявок ожидают рассмотрения',
                    'action': 'admin_review_registrations'
                })
            
            # Ближайшие турниры (завтра)
            tomorrow = date.today() + timedelta(days=1)
            tomorrow_tournaments = self.session.query(Tournament).filter(
                Tournament.date == tomorrow
            ).count()
            
            if tomorrow_tournaments > 0:
                alerts.append({
                    'type': 'info',
                    'message': f'🏆 Завтра {tomorrow_tournaments} турнир(ов)',
                    'action': 'admin_view_tournaments'
                })
            
        except Exception as e:
            logger.error(f"Ошибка при получении предупреждений: {e}")
        
        return alerts
    
    def _get_current_season_start(self) -> date:
        """Получает дату начала текущего сезона"""
        current_date = date.today()
        if current_date.month >= 9:  # Сентябрь и позже
            return date(current_date.year, 9, 1)
        else:  # До сентября
            return date(current_date.year - 1, 9, 1)
    
    def _get_current_season_end(self) -> date:
        """Получает дату окончания текущего сезона"""
        current_date = date.today()
        if current_date.month >= 9:  # Сентябрь и позже
            return date(current_date.year + 1, 5, 31)
        else:  # До сентября
            return date(current_date.year, 5, 31)
    
    async def _get_budget_stats(self) -> Dict[str, Any]:
        """Статистика по бюджетам турниров"""
        try:
            from models import TournamentBudget
            
            # Общая статистика по бюджетам
            total_budgets = self.session.query(func.sum(TournamentBudget.total_budget)).filter(
                TournamentBudget.total_budget.isnot(None)
            ).scalar() or 0
            
            total_judges_payment = self.session.query(func.sum(TournamentBudget.judges_payment)).filter(
                TournamentBudget.judges_payment.isnot(None)
            ).scalar() or 0
            
            total_admin_profit = self.session.query(func.sum(TournamentBudget.admin_profit)).filter(
                TournamentBudget.admin_profit.isnot(None)
            ).scalar() or 0
            
            # Количество турниров с бюджетом
            tournaments_with_budget = self.session.query(TournamentBudget).count()
            
            # Средняя рентабельность
            avg_profitability = (total_admin_profit / total_budgets * 100) if total_budgets > 0 else 0
            
            return {
                'total_budgets': float(total_budgets),
                'total_judges_payment': float(total_judges_payment),
                'total_admin_profit': float(total_admin_profit),
                'tournaments_with_budget': tournaments_with_budget,
                'avg_profitability': round(avg_profitability, 1)
            }
        except Exception as e:
            logger.error(f"Ошибка при получении статистики по бюджетам: {e}")
            return {
                'total_budgets': 0.0,
                'total_judges_payment': 0.0,
                'total_admin_profit': 0.0,
                'tournaments_with_budget': 0,
                'avg_profitability': 0.0
            }

# Глобальный экземпляр сервиса
_dashboard_service = None

def get_dashboard_service() -> DashboardService:
    """Получает экземпляр сервиса дашборда"""
    global _dashboard_service
    if _dashboard_service is None:
        _dashboard_service = DashboardService()
    return _dashboard_service
