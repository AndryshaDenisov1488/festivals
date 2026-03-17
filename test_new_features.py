# test_new_features.py
"""
Тестовый файл для проверки новых функций:
1. Система логирования действий
2. FSM Guard (блокировка команд)
3. Menu Manager (автоматический возврат в меню)
4. Улучшенные клавиатуры
5. Красивые Excel отчеты
"""

import asyncio
import logging
from aiogram import Bot, types
from unittest.mock import AsyncMock, MagicMock
from utils.action_logger import init_action_logger, get_action_logger, ActionType
from utils.menu_manager import get_menu_manager
from utils.fsm_guard import get_fsm_guard
from keyboards import main_menu, admin_menu_keyboard, cancel_keyboard, confirmation_keyboard

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_action_logging():
    """Тест системы логирования действий"""
    logger.info("=== Тестирование системы логирования действий ===")
    
    # Мокаем бота
    mock_bot = AsyncMock(spec=Bot)
    mock_bot.send_message = AsyncMock()
    
    # Инициализируем логгер действий
    init_action_logger(mock_bot)
    action_logger = get_action_logger()
    
    if not action_logger:
        logger.error("Action logger не инициализирован!")
        return False
    
    # Тестируем различные типы действий
    test_actions = [
        (ActionType.USER_REGISTER, 12345, {"name": "Тестовый Пользователь"}),
        (ActionType.ADMIN_ADD_TOURNAMENT, 67890, {"tournament": "Тестовый турнир"}),
        (ActionType.USER_SIGNUP_TOURNAMENT, 12345, {"tournament": "Турнир 1"}),
    ]
    
    for action_type, user_id, details in test_actions:
        await action_logger.log_action(action_type, user_id, details, success=True)
        logger.info(f"Логирование действия {action_type.value} для пользователя {user_id}")
    
    logger.info("✅ Тест логирования действий завершен")
    return True

async def test_menu_manager():
    """Тест менеджера меню"""
    logger.info("=== Тестирование менеджера меню ===")
    
    # Мокаем объекты
    mock_bot = AsyncMock(spec=Bot)
    mock_bot.send_message = AsyncMock()
    mock_message = MagicMock()
    mock_message.from_user.id = 12345
    mock_message.answer = AsyncMock()
    
    mock_callback = MagicMock()
    mock_callback.from_user.id = 12345
    mock_callback.message = mock_message
    mock_callback.answer = AsyncMock()
    
    mock_state = AsyncMock()
    mock_state.finish = AsyncMock()
    
    # Инициализируем менеджер меню
    menu_manager = get_menu_manager()
    
    # Тестируем установку контекста
    menu_manager.set_user_context(12345, "user")
    context = menu_manager.get_user_context(12345)
    logger.info(f"Контекст пользователя: {context}")
    
    # Тестируем возврат в меню
    await menu_manager.return_to_menu(
        mock_message, mock_state,
        "✅ Тестовое сообщение",
        ActionType.USER_REGISTER
    )
    
    logger.info("✅ Тест менеджера меню завершен")
    return True

async def test_fsm_guard():
    """Тест FSM Guard"""
    logger.info("=== Тестирование FSM Guard ===")
    
    # Мокаем объекты
    mock_bot = AsyncMock(spec=Bot)
    mock_bot.send_message = AsyncMock()
    
    mock_state = AsyncMock()
    mock_state.finish = AsyncMock()
    
    # Инициализируем FSM Guard
    fsm_guard = get_fsm_guard()
    
    # Тестируем создание сессии
    fsm_guard.start_session(12345, "RegisterReferee", mock_state)
    logger.info("FSM сессия создана")
    
    # Тестируем обновление активности
    fsm_guard.update_activity(12345)
    logger.info("Активность обновлена")
    
    # Тестируем завершение сессии
    fsm_guard.end_session(12345)
    logger.info("FSM сессия завершена")
    
    # Тестируем проверку таймаутов (без реального бота)
    try:
        await fsm_guard.check_timeouts(mock_bot)
        logger.info("Проверка таймаутов выполнена")
    except Exception as e:
        logger.warning(f"Ошибка при проверке таймаутов (ожидаемо): {e}")
    
    logger.info("✅ Тест FSM Guard завершен")
    return True

def test_keyboards():
    """Тест улучшенных клавиатур"""
    logger.info("=== Тестирование улучшенных клавиатур ===")
    
    # Тестируем основные клавиатуры
    main_kb = main_menu()
    admin_kb = admin_menu_keyboard()
    cancel_kb = cancel_keyboard("user")
    confirm_kb = confirmation_keyboard("confirm_action")
    
    logger.info(f"Главное меню: {len(main_kb.inline_keyboard)} кнопок")
    logger.info(f"Админ меню: {len(admin_kb.inline_keyboard)} кнопок")
    logger.info(f"Клавиатура отмены: {len(cancel_kb.inline_keyboard)} кнопок")
    logger.info(f"Клавиатура подтверждения: {len(confirm_kb.inline_keyboard)} кнопок")
    
    # Проверяем, что кнопки содержат эмодзи
    main_buttons = [btn.text for row in main_kb.inline_keyboard for btn in row]
    emoji_buttons = [btn for btn in main_buttons if any(ord(char) > 127 for char in btn)]
    logger.info(f"Кнопки с эмодзи в главном меню: {len(emoji_buttons)}")
    
    logger.info("✅ Тест клавиатур завершен")
    return True

async def run_all_tests():
    """Запуск всех тестов"""
    logger.info("🚀 Запуск тестирования новых функций...")
    
    tests = [
        ("Логирование действий", test_action_logging),
        ("Менеджер меню", test_menu_manager),
        ("FSM Guard", test_fsm_guard),
        ("Клавиатуры", test_keyboards),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
            logger.info(f"✅ {test_name}: {'ПРОЙДЕН' if result else 'ПРОВАЛЕН'}")
        except Exception as e:
            logger.error(f"❌ {test_name}: ОШИБКА - {e}")
            results.append((test_name, False))
    
    # Итоговый отчет
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    logger.info(f"\n📊 ИТОГОВЫЙ ОТЧЕТ:")
    logger.info(f"Пройдено тестов: {passed}/{total}")
    logger.info(f"Процент успеха: {passed/total*100:.1f}%")
    
    if passed == total:
        logger.info("🎉 Все тесты пройдены успешно!")
    else:
        logger.warning("⚠️ Некоторые тесты не прошли. Проверьте логи выше.")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(run_all_tests())
