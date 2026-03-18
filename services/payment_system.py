# services/payment_system.py
"""
Система отслеживания оплаты судей
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from sqlalchemy.exc import DatabaseError
import sqlite3
import pytz

from models import JudgePayment, User, Tournament, Registration, RegistrationStatus
from database import SessionLocal
from utils.action_logger import get_action_logger, ActionType

logger = logging.getLogger(__name__)

class PaymentSystem:
    """Класс для управления системой оплаты судей"""
    
    def __init__(self, bot):
        self.bot = bot
        self.action_logger = get_action_logger()
    
    async def create_payment_records(self, tournament_id: int) -> bool:
        """Создает записи об оплате для всех утвержденных судей турнира"""
        session = SessionLocal()
        
        try:
            # Получаем турнир
            tournament = session.query(Tournament).filter(Tournament.tournament_id == tournament_id).first()
            if not tournament:
                logger.error(f"Турнир с ID {tournament_id} не найден")
                return False
            
            # Получаем всех утвержденных судей
            approved_judges = session.query(Registration).filter(
                and_(
                    Registration.tournament_id == tournament_id,
                    Registration.status == RegistrationStatus.APPROVED
                )
            ).all()
            
            if not approved_judges:
                logger.warning(f"Нет утвержденных судей для турнира {tournament.name}")
                return False
            
            # Создаем записи об оплате
            created_count = 0
            for registration in approved_judges:
                # Проверяем, не создана ли уже запись
                existing_payment = session.query(JudgePayment).filter(
                    and_(
                        JudgePayment.user_id == registration.user_id,
                        JudgePayment.tournament_id == tournament_id
                    )
                ).first()
                
                if not existing_payment:
                    payment = JudgePayment(
                        user_id=registration.user_id,
                        tournament_id=tournament_id,
                        is_paid=False,
                        reminder_sent=False
                    )
                    session.add(payment)
                    created_count += 1
            
            # ВАЖНО: Удаляем записи об оплате для судей, которые больше не утверждены
            # Это синхронизирует записи об оплате с фактическим статусом регистраций
            all_payments = session.query(JudgePayment).filter(
                JudgePayment.tournament_id == tournament_id
            ).all()
            
            deleted_count = 0
            for payment in all_payments:
                # Проверяем, существует ли еще утвержденная регистрация
                registration = session.query(Registration).filter(
                    and_(
                        Registration.user_id == payment.user_id,
                        Registration.tournament_id == tournament_id,
                        Registration.status == RegistrationStatus.APPROVED
                    )
                ).first()
                
                if not registration:
                    # Регистрация не существует или не утверждена - удаляем запись об оплате
                    session.delete(payment)
                    deleted_count += 1
                    logger.info(
                        f"Удалена запись об оплате для user_id={payment.user_id} "
                        f"на турнир {tournament.name}: регистрация не найдена или не утверждена"
                    )
            
            session.commit()
            logger.info(
                f"Создано {created_count} записей об оплате для турнира {tournament.name}, "
                f"удалено {deleted_count} устаревших записей"
            )
            
            # Логируем действие
            if self.action_logger:
                await self.action_logger.log_action(
                    ActionType.ADMIN_CREATE_PAYMENT_RECORDS,
                    f"Созданы записи об оплате для турнира {tournament.name} ({created_count} судей, удалено {deleted_count} устаревших)"
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при создании записей об оплате: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    async def sync_payment_records_for_today(self) -> dict:
        """
        Синхронизирует записи об оплате для турниров, которые проходят сегодня.
        Создает записи для фактически утвержденных судей и удаляет записи для тех, кто не утвержден.
        Возвращает словарь с результатами синхронизации.
        """
        session = SessionLocal()
        result = {
            'created': 0,
            'deleted': 0,
            'tournaments_processed': 0
        }
        
        try:
            # Находим турниры, которые проходят сегодня (используем MSK timezone)
            msk_tz = pytz.timezone('Europe/Moscow')
            today = datetime.now(msk_tz).date()
            
            tournaments_today = session.query(Tournament).filter(
                Tournament.date == today
            ).all()
            
            if not tournaments_today:
                logger.info(f"Нет турниров на сегодня ({today})")
                return result
            
            for tournament in tournaments_today:
                result['tournaments_processed'] += 1
                
                # Получаем всех фактически утвержденных судей
                approved_judges = session.query(Registration).filter(
                    and_(
                        Registration.tournament_id == tournament.tournament_id,
                        Registration.status == RegistrationStatus.APPROVED
                    )
                ).all()
                
                # Создаем записи об оплате для утвержденных судей
                for registration in approved_judges:
                    existing_payment = session.query(JudgePayment).filter(
                        and_(
                            JudgePayment.user_id == registration.user_id,
                            JudgePayment.tournament_id == tournament.tournament_id
                        )
                    ).first()
                    
                    if not existing_payment:
                        payment = JudgePayment(
                            user_id=registration.user_id,
                            tournament_id=tournament.tournament_id,
                            is_paid=False,
                            reminder_sent=False
                        )
                        session.add(payment)
                        result['created'] += 1
                        logger.info(
                            f"Создана запись об оплате для user_id={registration.user_id} "
                            f"на турнир {tournament.name} (синхронизация в день турнира)"
                        )
                
                # Удаляем записи об оплате для судей, которые не утверждены
                all_payments = session.query(JudgePayment).filter(
                    JudgePayment.tournament_id == tournament.tournament_id
                ).all()
                
                for payment in all_payments:
                    registration = session.query(Registration).filter(
                        and_(
                            Registration.user_id == payment.user_id,
                            Registration.tournament_id == tournament.tournament_id,
                            Registration.status == RegistrationStatus.APPROVED
                        )
                    ).first()
                    
                    if not registration:
                        session.delete(payment)
                        result['deleted'] += 1
                        logger.info(
                            f"Удалена запись об оплате для user_id={payment.user_id} "
                            f"на турнир {tournament.name} (синхронизация в день турнира: регистрация не найдена или не утверждена)"
                        )
            
            session.commit()
            logger.info(
                f"Синхронизация записей об оплате для {result['tournaments_processed']} турниров: "
                f"создано {result['created']}, удалено {result['deleted']}"
            )
            
        except Exception as e:
            logger.error(f"Ошибка при синхронизации записей об оплате: {e}")
            session.rollback()
        finally:
            session.close()
        
        return result
    
    async def send_payment_reminders(self) -> int:
        """Отправляет напоминания об оплате судьям (в 18:00 в день турнира и каждые 12 часов)"""
        # ВАЖНО: Сначала синхронизируем записи об оплате для сегодняшних турниров
        # Это гарантирует, что напоминания отправляются только фактически утвержденным судьям
        await self.sync_payment_records_for_today()
        
        session = SessionLocal()
        reminders_sent = 0
        
        try:
            # Находим турниры, которые проходят сегодня (используем MSK timezone)
            msk_tz = pytz.timezone('Europe/Moscow')
            today = datetime.now(msk_tz).date()
            
            # Получаем все неоплаченные записи для турниров, которые проходят сегодня
            # Используем пагинацию для предотвращения утечек памяти
            unpaid_payments = session.query(JudgePayment).join(Tournament).filter(
                and_(
                    Tournament.date == today,
                    JudgePayment.is_paid == False
                )
            ).limit(100).all()  # Ограничиваем количество записей
            
            for payment in unpaid_payments:
                # ВАЖНО: Проверяем, что регистрация все еще существует и имеет статус APPROVED
                # Это предотвращает отправку напоминаний судьям, которые отменили запись
                registration = session.query(Registration).filter(
                    and_(
                        Registration.user_id == payment.user_id,
                        Registration.tournament_id == payment.tournament_id,
                        Registration.status == RegistrationStatus.APPROVED
                    )
                ).first()
                
                if not registration:
                    # Регистрация не существует или не утверждена - пропускаем это напоминание
                    logger.warning(
                        f"Пропущено напоминание для payment_id={payment.payment_id}: "
                        f"регистрация не найдена или не утверждена (user_id={payment.user_id}, tournament_id={payment.tournament_id})"
                    )
                    continue
                try:
                    # Проверяем, нужно ли отправить напоминание
                    should_send = False
                    msk_tz = pytz.timezone('Europe/Moscow')
                    now_msk = datetime.now(msk_tz)
                    today_msk = now_msk.date()
                    
                    # Ограничение: не отправляем напоминания после 7 дней с турнира
                    days_since_tournament = (today_msk - payment.tournament.date).days
                    MAX_REMINDER_DAYS = 7
                    
                    if days_since_tournament > MAX_REMINDER_DAYS:
                        # Прошло больше 7 дней - прекращаем напоминания
                        logger.info(
                            f"Пропущено напоминание для payment_id={payment.payment_id}: "
                            f"прошло {days_since_tournament} дней с турнира (максимум {MAX_REMINDER_DAYS})"
                        )
                        continue
                    
                    # Ограничение: максимум 5 напоминаний (первое + 4 повторных)
                    # Подсчитываем количество напоминаний по дате последнего напоминания
                    # Если reminder_date установлен, значит уже было хотя бы одно напоминание
                    MAX_REMINDERS = 5
                    reminder_count = 0
                    if payment.reminder_date:
                        # Приблизительно считаем количество напоминаний
                        # Первое напоминание в 18:00, затем каждые 6 часов
                        # За 7 дней максимум: 1 + (7*24/6) = 29, но мы ограничим до MAX_REMINDERS
                        # Используем более простую логику: если прошло больше 2 дней и было много напоминаний
                        hours_since_first = (now_msk - payment.reminder_date.replace(tzinfo=timezone.utc).astimezone(msk_tz)).total_seconds() / 3600
                        estimated_reminders = 1 + int(hours_since_first / 6)  # Первое + каждые 6 часов
                        if estimated_reminders >= MAX_REMINDERS:
                            logger.info(
                                f"Пропущено напоминание для payment_id={payment.payment_id}: "
                                f"достигнут лимит напоминаний (примерно {estimated_reminders})"
                            )
                            continue
                    
                    if not payment.reminder_sent:
                        # Первое напоминание в 18:00 в день турнира
                        if now_msk.hour >= 18:
                            should_send = True
                    elif payment.reminder_date:
                        # Проверяем, не установлена ли дата напоминания далеко в будущем
                        # (это означает, что судья уже ответил "Нет" и напоминания нужно прекратить)
                        last_reminder_msk = payment.reminder_date.replace(tzinfo=timezone.utc).astimezone(msk_tz)
                        days_until_reminder = (last_reminder_msk.date() - today_msk).days
                        
                        # Если дата напоминания больше чем через 30 дней - это специальная отметка
                        # что судья уже ответил и напоминания нужно прекратить
                        if days_until_reminder > 30:
                            logger.info(
                                f"Пропущено напоминание для payment_id={payment.payment_id}: "
                                f"судья уже ответил на напоминание"
                            )
                            continue
                        
                        # Повторные напоминания каждые 6 часов после первого
                        hours_since_last = (now_msk - last_reminder_msk).total_seconds() / 3600
                        if hours_since_last >= 6:
                            should_send = True
                    
                    if should_send:
                        # Отправляем напоминание судье
                        await self._send_payment_reminder(payment)
                        
                        # Отмечаем, что напоминание отправлено (используем UTC)
                        payment.reminder_sent = True
                        payment.reminder_date = datetime.now(timezone.utc)
                        reminders_sent += 1
                        
                except Exception as e:
                    logger.error(f"Ошибка при отправке напоминания судье {payment.user_id}: {e}")
            
            session.commit()
            logger.info(f"Отправлено {reminders_sent} напоминаний об оплате")
            
        except Exception as e:
            logger.error(f"Ошибка при отправке напоминаний: {e}")
            session.rollback()
        finally:
            session.close()
        
        return reminders_sent
    
    async def _send_payment_reminder(self, payment: JudgePayment):
        """Отправляет напоминание об оплате конкретному судье"""
        from keyboards import payment_reminder_keyboard
        
        # Определяем тип напоминания
        if not payment.reminder_sent:
            # Первое напоминание - вежливое
            message = (
                f"💰 <b>Напоминание об оплате</b>\n\n"
                f"Привет, {payment.user.first_name}!\n\n"
                f"Прошёл день с турнира <b>«{payment.tournament.name}»</b> "
                f"({payment.tournament.date.strftime('%d.%m.%Y')}).\n\n"
                f"Андрюша заплатил вам за этот турнир? 🤔"
            )
        else:
            # Повторное напоминание - более настойчивое
            days_since_tournament = (datetime.now().date() - payment.tournament.date).days
            message = (
                f"⚠️ <b>ПОВТОРНОЕ НАПОМИНАНИЕ ОБ ОПЛАТЕ</b>\n\n"
                f"Привет, {payment.user.first_name}!\n\n"
                f"Прошло уже <b>{days_since_tournament} дней</b> с турнира <b>«{payment.tournament.name}»</b> "
                f"({payment.tournament.date.strftime('%d.%m.%Y')}).\n\n"
                f"Андрюша заплатил вам за этот турнир? 🤔\n\n"
                f"<i>Пожалуйста, ответьте, чтобы мы могли отследить оплату!</i>"
            )
        
        await self.bot.send_message(
            chat_id=payment.user.user_id,
            text=message,
            reply_markup=payment_reminder_keyboard(payment.payment_id),
            parse_mode='HTML'
        )
        if payment.user.email:
            try:
                from api.email_service import send_payment_reminder_email
                send_payment_reminder_email(
                    payment.user.email,
                    payment.user.first_name,
                    payment.tournament.name,
                    payment.tournament.date.strftime('%d.%m.%Y'),
                    is_repeat=payment.reminder_sent
                )
            except Exception as e:
                logger.exception("Ошибка отправки email напоминания об оплате: %s", e)
    
    async def handle_payment_confirmation(self, payment_id: int, is_paid: bool, amount: Optional[float] = None):
        """Обрабатывает подтверждение оплаты от судьи"""
        session = SessionLocal()
        
        try:
            payment = session.query(JudgePayment).filter(JudgePayment.payment_id == payment_id).first()
            if not payment:
                logger.error(f"Запись об оплате с ID {payment_id} не найдена")
                return False
            
            if is_paid:
                # Судья подтвердил оплату
                payment.is_paid = True
                payment.payment_date = datetime.utcnow()
                if amount:
                    payment.amount = amount
                
                # Отправляем саркастическое сообщение
                sarcastic_messages = [
                    "Вам повезло! 🍀",
                    "Невероятно! 🤯",
                    "Это же чудо! ✨",
                    "Андрюша наконец-то заплатил! 🎉",
                    "Не может быть! 😱"
                ]
                
                import random
                sarcastic_msg = random.choice(sarcastic_messages)
                
                if amount:
                    message = (
                        f"{sarcastic_msg}\n\n"
                        f"💰 Сумма: {amount} руб.\n"
                        f"📅 Дата: {payment.tournament.date.strftime('%d.%m.%Y')}\n"
                        f"🏆 Турнир: {payment.tournament.name}\n\n"
                        f"Спасибо за работу! 🙏"
                    )
                else:
                    message = (
                        f"{sarcastic_msg}\n\n"
                        f"📅 Дата: {payment.tournament.date.strftime('%d.%m.%Y')}\n"
                        f"🏆 Турнир: {payment.tournament.name}\n\n"
                        f"Спасибо за работу! 🙏"
                    )
                
                if self.bot:
                    await self.bot.send_message(
                        chat_id=payment.user.user_id,
                        text=message,
                        parse_mode='HTML'
                    )
                
                # Обновляем бюджет турнира
                from services.budget_service import get_budget_service
                budget_service = get_budget_service(self.bot)
                await budget_service.update_judges_payment(payment.tournament_id)
                
                # Логируем действие (только если есть bot — action_logger может использовать его)
                if self.action_logger and self.bot:
                    await self.action_logger.log_action(
                        ActionType.USER_CONFIRM_PAYMENT,
                        f"Судья {payment.user.first_name} {payment.user.last_name} подтвердил оплату за турнир {payment.tournament.name}"
                    )
                
            else:
                # Судья не получил оплату - уведомляем админа (только если есть bot)
                if self.bot:
                    await self._notify_admin_about_unpaid_judge(payment)
                
                # ВАЖНО: Устанавливаем reminder_date далеко в будущем, чтобы прекратить отправку напоминаний
                # Судья уже ответил, админ уведомлен - больше не нужно "дергать" судью
                from datetime import timedelta
                payment.reminder_date = datetime.now(timezone.utc) + timedelta(days=365)  # Через год
                payment.reminder_sent = True  # Отмечаем как отправленное, чтобы не отправлять больше
                
                # Логируем действие
                if self.action_logger:
                    await self.action_logger.log_action(
                        ActionType.USER_REPORT_UNPAID,
                        f"Судья {payment.user.first_name} {payment.user.last_name} сообщил о неоплате за турнир {payment.tournament.name}"
                    )
            
            session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при обработке подтверждения оплаты: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    async def _notify_admin_about_unpaid_judge(self, payment: JudgePayment):
        """Уведомляет админа о неоплаченном судье"""
        from config import ADMIN_IDS
        
        message = (
            f"⚠️ <b>ВНИМАНИЕ! Неоплаченный судья</b>\n\n"
            f"👤 <b>Судья:</b> {payment.user.first_name} {payment.user.last_name}\n"
            f"🏆 <b>Турнир:</b> {payment.tournament.name}\n"
            f"📅 <b>Дата:</b> {payment.tournament.date.strftime('%d.%m.%Y')}\n\n"
            f"💸 <b>ОПЛАТИ, ИНАЧЕ У ТЕБЯ НЕ БУДУТ СУДИТЬ!</b> 😤"
        )
        
        for admin_id in ADMIN_IDS:
            try:
                await self.bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления админу {admin_id}: {e}")
    
    async def send_admin_reminders(self) -> int:
        """Отправляет напоминания админу о неоплаченных судьях в 18:00 в день турнира и каждые 6 часов после"""
        session = SessionLocal()
        reminders_sent = 0
        
        try:
            # Находим турниры, которые проходят сегодня (используем MSK timezone)
            msk_tz = pytz.timezone('Europe/Moscow')
            now_msk = datetime.now(msk_tz)
            today = now_msk.date()
            
            # ВАЖНО: Напоминания админу отправляем только в 18:00 и позже в день турнира
            # Не отправляем в 00:00, 06:00, 12:00 - только в 18:00 и каждые 6 часов после
            if now_msk.hour < 18:
                logger.info(f"Напоминания админу пропущены: текущее время {now_msk.hour}:{now_msk.minute:02d}, требуется >= 18:00")
                return 0
            
            # Получаем все неоплаченные записи для турниров, которые проходят сегодня
            unpaid_payments = session.query(JudgePayment).join(Tournament).filter(
                and_(
                    Tournament.date == today,
                    JudgePayment.is_paid == False
                )
            ).limit(100).all()
            
            # Фильтруем только те, где регистрация все еще существует и утверждена
            valid_unpaid_payments = []
            for payment in unpaid_payments:
                registration = session.query(Registration).filter(
                    and_(
                        Registration.user_id == payment.user_id,
                        Registration.tournament_id == payment.tournament_id,
                        Registration.status == RegistrationStatus.APPROVED
                    )
                ).first()
                if registration:
                    valid_unpaid_payments.append(payment)
            
            if not valid_unpaid_payments:
                return 0
            
            # Группируем по турнирам
            tournaments_unpaid = {}
            for payment in valid_unpaid_payments:
                tournament_id = payment.tournament_id
                if tournament_id not in tournaments_unpaid:
                    tournaments_unpaid[tournament_id] = {
                        'tournament': payment.tournament,
                        'unpaid_judges': []
                    }
                tournaments_unpaid[tournament_id]['unpaid_judges'].append(payment.user)
            
            # Отправляем уведомления админу
            from config import ADMIN_IDS
            for admin_id in ADMIN_IDS:
                for tournament_id, data in tournaments_unpaid.items():
                    tournament = data['tournament']
                    unpaid_judges = data['unpaid_judges']
                    
                    judges_list = "\n".join([f"• {judge.first_name} {judge.last_name}" for judge in unpaid_judges])
                    
                    message = (
                        f"🚨 <b>НАПОМИНАНИЕ АДМИНУ</b>\n\n"
                        f"🏆 <b>Турнир:</b> {tournament.name}\n"
                        f"📅 <b>Дата:</b> {tournament.date.strftime('%d.%m.%Y')}\n"
                        f"👥 <b>Неоплаченных судей:</b> {len(unpaid_judges)}\n\n"
                        f"<b>Список судей:</b>\n{judges_list}\n\n"
                        f"💸 <b>ОПЛАТИ ИМ, ИНАЧЕ НЕ БУДУТ СУДИТЬ!</b> 😤"
                    )
                    
                    try:
                        await self.bot.send_message(
                            chat_id=admin_id,
                            text=message,
                            parse_mode='HTML'
                        )
                        reminders_sent += 1
                    except Exception as e:
                        logger.error(f"Ошибка при отправке напоминания админу {admin_id}: {e}")
            
            logger.info(f"Отправлено {reminders_sent} напоминаний админу о неоплаченных судьях")
            
        except Exception as e:
            logger.error(f"Ошибка при отправке напоминаний админу: {e}")
        finally:
            session.close()
        
        return reminders_sent
    
    def get_judge_earnings(self, user_id: int) -> dict:
        """Получает информацию о заработке судьи"""
        session = SessionLocal()
        
        try:
            # Общая статистика
            total_tournaments = session.query(JudgePayment).filter(
                and_(
                    JudgePayment.user_id == user_id,
                    JudgePayment.is_paid == True
                )
            ).count()
            
            total_amount = session.query(func.sum(JudgePayment.amount)).filter(
                and_(
                    JudgePayment.user_id == user_id,
                    JudgePayment.is_paid == True,
                    JudgePayment.amount.isnot(None)
                )
            ).scalar() or 0
            
            # Детальная информация по турнирам
            tournament_earnings = session.query(
                Tournament.name,
                Tournament.date,
                JudgePayment.amount,
                JudgePayment.payment_date
            ).join(JudgePayment).filter(
                and_(
                    JudgePayment.user_id == user_id,
                    JudgePayment.is_paid == True
                )
            ).order_by(Tournament.date.desc()).all()
            
            # Заработок по месяцам
            monthly_earnings = session.query(
                func.strftime('%Y-%m', Tournament.date).label('month'),
                func.sum(JudgePayment.amount).label('total_amount'),
                func.count(JudgePayment.payment_id).label('tournaments_count')
            ).join(JudgePayment).filter(
                and_(
                    JudgePayment.user_id == user_id,
                    JudgePayment.is_paid == True,
                    JudgePayment.amount.isnot(None)
                )
            ).group_by(func.strftime('%Y-%m', Tournament.date)).order_by('month').all()
            
            return {
                'total_tournaments': total_tournaments,
                'total_amount': total_amount,
                'tournament_earnings': tournament_earnings,
                'monthly_earnings': monthly_earnings
            }
            
        except (DatabaseError, sqlite3.DatabaseError) as e:
            error_msg = str(e)
            if "malformed" in error_msg.lower():
                logger.critical(f"База данных повреждена при получении заработка судьи {user_id}: {e}")
                logger.critical("ТРЕБУЕТСЯ ВОССТАНОВЛЕНИЕ БАЗЫ ДАННЫХ! Запустите: python repair_database.py")
            else:
                logger.error(f"Ошибка базы данных при получении заработка судьи {user_id}: {e}")
            return {
                'total_tournaments': 0,
                'total_amount': 0,
                'tournament_earnings': [],
                'monthly_earnings': []
            }
        except Exception as e:
            logger.error(f"Ошибка при получении заработка судьи {user_id}: {e}")
            return {
                'total_tournaments': 0,
                'total_amount': 0,
                'tournament_earnings': [],
                'monthly_earnings': []
            }
        finally:
            session.close()

# Глобальный экземпляр
_payment_system = None

def get_payment_system(bot=None):
    """Получает экземпляр системы оплаты"""
    global _payment_system
    if _payment_system is None and bot:
        _payment_system = PaymentSystem(bot)
    return _payment_system
