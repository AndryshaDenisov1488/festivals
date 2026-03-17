# utils/fsm_guard.py
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
from aiogram import types
from aiogram.dispatcher import FSMContext
from states import (
    RegisterReferee, AddTournament, EditTournament, EditProfile, 
    MyRegistrations, CheckRegistrations, SendAllMessages, DeleteTournament,
    PaymentAmount, BudgetInput
)

logger = logging.getLogger(__name__)

class FSMGuard:
    """Система автоматического завершения FSM состояний по таймауту"""
    
    def __init__(self):
        # Таймауты для разных FSM состояний (в минутах)
        self.timeouts = {
            "RegisterReferee": 10,  # 10 минут на регистрацию
            "AddTournament": 15,    # 15 минут на добавление турнира
            "EditTournament": 15,   # 15 минут на редактирование турнира
            "EditProfile": 10,      # 10 минут на редактирование профиля
            "MyRegistrations": 5,   # 5 минут на просмотр записей
            "CheckRegistrations": 10, # 10 минут на проверку записей
            "SendAllMessages": 10,  # 10 минут на отправку сообщения
            "DeleteTournament": 5,  # 5 минут на удаление турнира
            "PaymentAmount": 5,     # 5 минут на ввод суммы оплаты
            "BudgetInput": 5,       # 5 минут на ввод бюджета
            "CorrectEarnings": 5,   # 5 минут на исправление заработка
        }
        
        # Активные FSM сессии с временными метками
        self.active_sessions: Dict[int, Dict] = {}
        
        # Запускаем фоновую задачу очистки
        self._cleanup_task = None
    
    def start_session(self, user_id: int, state_name: str, state: FSMContext):
        """Начинает отслеживание FSM сессии"""
        timeout_minutes = self.timeouts.get(state_name, 10)  # По умолчанию 10 минут
        
        self.active_sessions[user_id] = {
            "state_name": state_name,
            "state": state,
            "start_time": datetime.now(),
            "timeout_minutes": timeout_minutes,
            "last_activity": datetime.now()
        }
        
        logger.info(f"FSM сессия начата для пользователя {user_id}: {state_name} (таймаут: {timeout_minutes} мин)")
    
    def update_activity(self, user_id: int):
        """Обновляет время последней активности"""
        if user_id in self.active_sessions:
            self.active_sessions[user_id]["last_activity"] = datetime.now()
    
    def end_session(self, user_id: int):
        """Завершает FSM сессию"""
        if user_id in self.active_sessions:
            session = self.active_sessions[user_id]
            logger.info(f"FSM сессия завершена для пользователя {user_id}: {session['state_name']}")
            del self.active_sessions[user_id]
    
    async def check_timeouts(self, bot):
        """Проверяет и завершает просроченные сессии"""
        now = datetime.now()
        expired_sessions = []
        
        for user_id, session in self.active_sessions.items():
            last_activity = session["last_activity"]
            timeout_minutes = session["timeout_minutes"]
            
            # Проверяем, истек ли таймаут
            if now - last_activity > timedelta(minutes=timeout_minutes):
                expired_sessions.append(user_id)
        
        # Завершаем просроченные сессии
        for user_id in expired_sessions:
            session = self.active_sessions[user_id]
            state_name = session["state_name"]
            
            try:
                # Завершаем FSM состояние
                await session["state"].finish()
                
                # Отправляем уведомление пользователю
                timeout_message = self._get_timeout_message(state_name)
                await bot.send_message(user_id, timeout_message)
                
                logger.info(f"FSM сессия завершена по таймауту для пользователя {user_id}: {state_name}")
                
            except Exception as e:
                logger.error(f"Ошибка при завершении FSM сессии {user_id}: {e}")
            finally:
                del self.active_sessions[user_id]
    
    def _get_timeout_message(self, state_name: str) -> str:
        """Возвращает сообщение о завершении по таймауту"""
        messages = {
            "RegisterReferee": "⏰ <b>Время регистрации истекло</b>\n\nРегистрация была автоматически отменена из-за неактивности. Используйте /start для начала заново.",
            "AddTournament": "⏰ <b>Время добавления турнира истекло</b>\n\nПроцесс добавления турнира был автоматически отменен. Используйте /admin для возврата в админ-меню.",
            "EditTournament": "⏰ <b>Время редактирования турнира истекло</b>\n\nПроцесс редактирования был автоматически отменен. Используйте /admin для возврата в админ-меню.",
            "EditProfile": "⏰ <b>Время редактирования профиля истекло</b>\n\nРедактирование профиля было автоматически отменено. Используйте /start для возврата в главное меню.",
            "MyRegistrations": "⏰ <b>Время просмотра записей истекло</b>\n\nПросмотр записей был автоматически завершен. Используйте /start для возврата в главное меню.",
            "CheckRegistrations": "⏰ <b>Время проверки записей истекло</b>\n\nПроверка записей была автоматически завершена. Используйте /admin для возврата в админ-меню.",
            "SendAllMessages": "⏰ <b>Время отправки сообщения истекло</b>\n\nОтправка сообщения была автоматически отменена. Используйте /admin для возврата в админ-меню.",
            "DeleteTournament": "⏰ <b>Время удаления турнира истекло</b>\n\nУдаление турнира было автоматически отменено. Используйте /admin для возврата в админ-меню.",
            "PaymentAmount": "⏰ <b>Время ввода суммы оплаты истекло</b>\n\nВвод суммы был автоматически отменен. Вы можете вернуться к этому позже через меню заработка.",
            "BudgetInput": "⏰ <b>Время ввода бюджета истекло</b>\n\nВвод бюджета был автоматически отменен. Используйте /admin для возврата в админ-меню.",
            "CorrectEarnings": "⏰ <b>Время исправления заработка истекло</b>\n\nИсправление заработка было автоматически отменено. Вы можете вернуться к этому позже через меню заработка.",
        }
        return messages.get(state_name, "⏰ <b>Время выполнения операции истекло</b>\n\nОперация была автоматически отменена из-за неактивности.")
    
    async def start_cleanup_task(self, bot):
        """Запускает фоновую задачу очистки"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop(bot))
            logger.info("FSM Guard: Запущена фоновая задача очистки")
    
    async def _cleanup_loop(self, bot):
        """Фоновая задача для проверки таймаутов"""
        while True:
            try:
                await self.check_timeouts(bot)
                await asyncio.sleep(60)  # Проверяем каждую минуту
            except Exception as e:
                logger.error(f"Ошибка в FSM Guard cleanup loop: {e}")
                await asyncio.sleep(60)
    
    async def stop_cleanup_task(self):
        """Останавливает фоновую задачу очистки"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("FSM Guard: Фоновая задача очистки остановлена")
    

# Глобальный экземпляр
fsm_guard = FSMGuard()

def get_fsm_guard() -> FSMGuard:
    """Получение экземпляра FSM Guard"""
    return fsm_guard
