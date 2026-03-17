# utils/menu_manager.py
import logging
from typing import Optional, Union
from aiogram import types
from aiogram.dispatcher import FSMContext
from keyboards import main_menu, admin_menu_keyboard
from utils.action_logger import get_action_logger, ActionType

logger = logging.getLogger(__name__)

class MenuManager:
    """Менеджер для управления меню и навигацией"""
    
    def __init__(self):
        self.user_contexts = {}  # Хранение контекста пользователей
    
    def set_user_context(self, user_id: int, context: str):
        """Устанавливает контекст пользователя (user/admin)"""
        self.user_contexts[user_id] = context
    
    def get_user_context(self, user_id: int) -> str:
        """Получает контекст пользователя"""
        return self.user_contexts.get(user_id, "user")
    
    async def return_to_menu(
        self, 
        message_or_callback: Union[types.Message, types.CallbackQuery], 
        state: FSMContext,
        success_message: Optional[str] = None,
        log_action: Optional[ActionType] = None
    ):
        """
        Возвращает пользователя в соответствующее меню
        """
        try:
            # Завершаем FSM состояние
            await state.finish()
            
            # Определяем тип объекта
            if isinstance(message_or_callback, types.CallbackQuery):
                user_id = message_or_callback.from_user.id
                message = message_or_callback.message
                is_callback = True
            else:
                user_id = message_or_callback.from_user.id
                message = message_or_callback
                is_callback = False
            
            # Определяем контекст пользователя
            context = self.get_user_context(user_id)
            
            # Выбираем соответствующее меню
            if context == "admin":
                menu_keyboard = admin_menu_keyboard()
                menu_text = "🛠️ <b>Административное меню</b>\n\nВыберите действие:"
            else:
                menu_keyboard = main_menu()
                menu_text = "🏆 <b>Главное меню</b>\n\nВыберите действие:"
            
            # Отправляем сообщение
            if success_message:
                menu_text = f"{success_message}\n\n{menu_text}"
            
            if is_callback:
                await message.edit_text(menu_text, parse_mode="HTML", reply_markup=menu_keyboard)
                await message_or_callback.answer()
            else:
                await message.answer(menu_text, parse_mode="HTML", reply_markup=menu_keyboard)
            
            # Логируем действие если указано
            if log_action:
                action_logger = get_action_logger()
                if action_logger:
                    await action_logger.log_action(log_action, user_id, {"context": context})
            
            logger.info(f"User {user_id} returned to {context} menu")
            
        except Exception as e:
            logger.error(f"Error returning to menu for user {user_id}: {e}")
            # Fallback - просто отправляем команду
            if isinstance(message_or_callback, types.CallbackQuery):
                user_id = message_or_callback.from_user.id
                context = self.get_user_context(user_id)
                if context == "admin":
                    await message_or_callback.message.answer("🛠️ Административное меню:", reply_markup=admin_menu_keyboard())
                else:
                    await message_or_callback.message.answer("🏆 Главное меню:", reply_markup=main_menu())
            else:
                context = self.get_user_context(message_or_callback.from_user.id)
                if context == "admin":
                    await message_or_callback.answer("🛠️ Административное меню:", reply_markup=admin_menu_keyboard())
                else:
                    await message_or_callback.answer("🏆 Главное меню:", reply_markup=main_menu())
    
    async def handle_back_button(
        self,
        callback_query: types.CallbackQuery,
        state: FSMContext,
        custom_message: Optional[str] = None
    ):
        """
        Обрабатывает нажатие кнопки "Назад"
        """
        user_id = callback_query.from_user.id
        context = self.get_user_context(user_id)
        
        if custom_message:
            await self.return_to_menu(callback_query, state, custom_message)
        else:
            back_messages = {
                "admin": "🔙 Возврат в административное меню",
                "user": "🔙 Возврат в главное меню"
            }
            message = back_messages.get(context, "🔙 Возврат в меню")
            await self.return_to_menu(callback_query, state, message)

# Глобальный экземпляр
menu_manager = MenuManager()

def get_menu_manager() -> MenuManager:
    """Получение экземпляра менеджера меню"""
    return menu_manager
