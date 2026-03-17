# utils/action_logger.py
import logging
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from aiogram import Bot
from config import CHANNEL_ID, ENABLE_ERROR_MONITORING

logger = logging.getLogger(__name__)

class ActionType(Enum):
    # Пользовательские действия
    USER_REGISTER = "user_register"
    USER_EDIT_PROFILE = "user_edit_profile"
    USER_SIGNUP_TOURNAMENT = "user_signup_tournament"
    USER_CANCEL_REGISTRATION = "user_cancel_registration"
    USER_VIEW_REGISTRATIONS = "user_view_registrations"
    
    # Админские действия
    ADMIN_ADD_TOURNAMENT = "admin_add_tournament"
    ADMIN_EDIT_TOURNAMENT = "admin_edit_tournament"
    ADMIN_DELETE_TOURNAMENT = "admin_delete_tournament"
    ADMIN_APPROVE_REGISTRATION = "admin_approve_registration"
    ADMIN_REJECT_REGISTRATION = "admin_reject_registration"
    ADMIN_VIEW_TOURNAMENTS = "admin_view_tournaments"
    ADMIN_VIEW_REFEREES = "admin_view_referees"
    ADMIN_EXPORT_DATA = "admin_export_data"
    ADMIN_SEND_MESSAGE = "admin_send_message"
    
    # Системные действия
    SYSTEM_REMINDER = "system_reminder"
    SYSTEM_ERROR = "system_error"
    
    # Система оплаты
    ADMIN_CREATE_PAYMENT_RECORDS = "admin_create_payment_records"
    USER_CONFIRM_PAYMENT = "user_confirm_payment"
    USER_REPORT_UNPAID = "user_report_unpaid"
    ADMIN_MANUAL_PAYMENT = "admin_manual_payment"

class ActionLogger:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.enabled = ENABLE_ERROR_MONITORING and CHANNEL_ID
    
    async def log_action(
        self, 
        action_type: ActionType, 
        user_id_or_message, 
        details: Optional[Dict[str, Any]] = None,
        success: bool = True
    ):
        """
        Логирует действие пользователя
        """
        try:
            action_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            
            # Определяем тип пользователя
            user_type = "👤 Пользователь" if not action_type.value.startswith("admin_") else "👑 Админ"
            
            # Формируем сообщение
            emoji = "✅" if success else "❌"
            status = "успешно" if success else "с ошибкой"
            
            message = f"{emoji} <b>ДЕЙСТВИЕ ВЫПОЛНЕНО</b>\n\n"
            message += f"⏰ Время: {action_time}\n"
            
            # Если передан user_id (число), показываем его, иначе показываем сообщение
            if isinstance(user_id_or_message, int):
                message += f"{user_type}: {user_id_or_message}\n"
            else:
                message += f"📝 Сообщение: {user_id_or_message}\n"
            
            message += f"🔧 Действие: {self._get_action_description(action_type)}\n"
            message += f"📊 Статус: {status}\n"
            
            if details:
                message += f"\n📝 Детали:\n"
                for key, value in details.items():
                    message += f"• <b>{key}:</b> {value}\n"
            
            # Логируем в файл
            if isinstance(user_id_or_message, int):
                log_message = f"[{action_time}] {action_type.value} by user {user_id_or_message} - {status}"
            else:
                log_message = f"[{action_time}] {action_type.value}: {user_id_or_message} - {status}"
            if details:
                log_message += f" | Details: {details}"
            logger.info(log_message)
            
            # Отправляем в канал (только для важных действий)
            if self.enabled and self._should_send_to_channel(action_type):
                await self.bot.send_message(
                    CHANNEL_ID,
                    message,
                    parse_mode="HTML"
                )
                
        except Exception as e:
            logger.error(f"Failed to log action: {e}")
    
    def _get_action_description(self, action_type: ActionType) -> str:
        """Возвращает описание действия на русском языке"""
        descriptions = {
            ActionType.USER_REGISTER: "Регистрация пользователя",
            ActionType.USER_EDIT_PROFILE: "Редактирование профиля",
            ActionType.USER_SIGNUP_TOURNAMENT: "Запись на турнир",
            ActionType.USER_CANCEL_REGISTRATION: "Отмена записи на турнир",
            ActionType.USER_VIEW_REGISTRATIONS: "Просмотр своих записей",
            ActionType.ADMIN_ADD_TOURNAMENT: "Добавление турнира",
            ActionType.ADMIN_EDIT_TOURNAMENT: "Редактирование турнира",
            ActionType.ADMIN_DELETE_TOURNAMENT: "Удаление турнира",
            ActionType.ADMIN_APPROVE_REGISTRATION: "Утверждение заявки",
            ActionType.ADMIN_REJECT_REGISTRATION: "Отклонение заявки",
            ActionType.ADMIN_VIEW_TOURNAMENTS: "Просмотр турниров",
            ActionType.ADMIN_VIEW_REFEREES: "Просмотр судей",
            ActionType.ADMIN_EXPORT_DATA: "Экспорт данных",
            ActionType.ADMIN_SEND_MESSAGE: "Отправка сообщения всем",
            ActionType.SYSTEM_REMINDER: "Системное напоминание",
            ActionType.SYSTEM_ERROR: "Системная ошибка",
            ActionType.ADMIN_CREATE_PAYMENT_RECORDS: "Создание записей об оплате",
            ActionType.USER_CONFIRM_PAYMENT: "Подтверждение оплаты",
            ActionType.USER_REPORT_UNPAID: "Сообщение о неоплате",
            ActionType.ADMIN_MANUAL_PAYMENT: "Ручной ввод заработка админом"
        }
        return descriptions.get(action_type, action_type.value)
    
    def _should_send_to_channel(self, action_type: ActionType) -> bool:
        """Определяет, нужно ли отправлять действие в канал"""
        important_actions = {
            ActionType.ADMIN_ADD_TOURNAMENT,
            ActionType.ADMIN_EDIT_TOURNAMENT,
            ActionType.ADMIN_DELETE_TOURNAMENT,
            ActionType.ADMIN_APPROVE_REGISTRATION,
            ActionType.ADMIN_REJECT_REGISTRATION,
            ActionType.ADMIN_SEND_MESSAGE,
            ActionType.SYSTEM_ERROR
        }
        return action_type in important_actions

# Глобальный экземпляр
action_logger = None

def init_action_logger(bot: Bot):
    """Инициализация логгера действий"""
    global action_logger
    action_logger = ActionLogger(bot)
    return action_logger

def get_action_logger() -> ActionLogger:
    """Получение экземпляра логгера действий"""
    return action_logger
