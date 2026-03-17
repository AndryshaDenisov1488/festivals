import logging
import re
from aiogram import types
from aiogram.dispatcher import FSMContext
from database import SessionLocal
from models import User
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from states import RegisterReferee
from keyboards import main_menu
from config import ADMIN_IDS
from aiogram.types import ParseMode

logger = logging.getLogger(__name__)

# Разрешаем буквы RU/EN + дефис, длина 2..30
_NAME_RE = re.compile(r"^[A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё\-]{1,29}$")


async def cmd_start(message: types.Message, state: FSMContext):
    """
    Обработчик команды /start
    """
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.user_id == message.from_user.id).first()
        if user:
            logger.info(f"Пользователь {message.from_user.id} уже зарегистрирован.")
            # Устанавливаем контекст пользователя как обычный пользователь
            from utils.menu_manager import get_menu_manager
            menu_manager = get_menu_manager()
            menu_manager.set_user_context(message.from_user.id, "user")
            await message.answer(f"👋 С возвращением, {user.first_name}!", reply_markup=main_menu())
        else:
            logger.info(f"Пользователь {message.from_user.id} начал регистрацию.")
            
            # Начинаем отслеживание FSM сессии
            from utils.fsm_guard import get_fsm_guard
            fsm_guard = get_fsm_guard()
            fsm_guard.start_session(message.from_user.id, "RegisterReferee", state)
            
            await message.answer(
                "👋 Привет! Давай зарегистрируемся.\n\nВведите ваше <b>имя</b>:",
                parse_mode=ParseMode.HTML
            )
            await RegisterReferee.waiting_for_first_name.set()
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при проверке пользователя {message.from_user.id}: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")
    finally:
        session.close()


async def process_first_name(message: types.Message, state: FSMContext):
    """
    Шаг FSM: ввод имени
    Мягкая валидация:
      - только буквы (RU/EN) и дефис
      - длина 2..30
      - фильтруем не-текстовые сообщения
    """
    try:
        if not getattr(message, "text", None):
            await message.answer(
                "❌ Мне нужен текст. Пожалуйста, введите ваше <b>имя</b> буквами.",
                parse_mode=ParseMode.HTML
            )
            return

        first_name = (message.text or "").strip()
        # нормализация пробелов
        first_name = re.sub(r"\s+", " ", first_name)

        if not _NAME_RE.match(first_name):
            await message.answer(
                "❌ Пожалуйста, введите корректное <b>имя</b>:\n"
                "• только буквы (рус/англ) и дефис\n"
                "• длина от 2 до 30 символов\n\n"
                "Например: <code>Андрей</code> или <code>Анна-Мария</code>",
                parse_mode=ParseMode.HTML,
            )
            return

        await state.update_data(first_name=first_name)
        await message.answer("Введите вашу <b>фамилию</b>:", parse_mode=ParseMode.HTML)
        await RegisterReferee.next()
        logger.info("Register FSM: first_name accepted: %r (user_id=%s)", first_name, message.from_user.id)

    except Exception as e:
        logger.exception("process_first_name failed (user_id=%s): %s", getattr(message.from_user, "id", None), e)
        await message.answer("⚠️ Произошла ошибка при обработке имени. Повторите ввод, пожалуйста.")


async def process_last_name(message: types.Message, state: FSMContext):
    """
    Шаг FSM: ввод фамилии
    Те же правила, что и для имени.
    """
    try:
        if not getattr(message, "text", None):
            await message.answer(
                "❌ Мне нужен текст. Пожалуйста, введите вашу <b>фамилию</b> буквами.",
                parse_mode=ParseMode.HTML
            )
            return

        last_name = (message.text or "").strip()
        last_name = re.sub(r"\s+", " ", last_name)

        if not _NAME_RE.match(last_name):
            await message.answer(
                "❌ Пожалуйста, введите корректную <b>фамилию</b>:\n"
                "• только буквы (рус/англ) и дефис\n"
                "• длина от 2 до 30 символов",
                parse_mode=ParseMode.HTML,
            )
            return

        await state.update_data(last_name=last_name)
        await message.answer("Введите вашу <b>судейскую функцию</b> (например, Главный судья):", parse_mode=ParseMode.HTML)
        await RegisterReferee.next()
        logger.info("Register FSM: last_name accepted: %r (user_id=%s)", last_name, message.from_user.id)

    except Exception as e:
        logger.exception("process_last_name failed (user_id=%s): %s", getattr(message.from_user, "id", None), e)
        await message.answer("⚠️ Произошла ошибка при обработке фамилии. Повторите ввод, пожалуйста.")


async def process_function(message: types.Message, state: FSMContext):
    """
    Шаг FSM: ввод судейской функции
    - Проверяем, что пришёл текст
    - Длина 2..60 символов
    """
    try:
        if not getattr(message, "text", None):
            await message.answer("❌ Пожалуйста, отправьте текст с вашей судейской функцией.")
            return

        function = (message.text or "").strip()
        function = re.sub(r"\s+", " ", function)

        if not (2 <= len(function) <= 60):
            await message.answer("❌ Поле не может быть пустым. Введите вашу судейскую функцию (2–60 символов):")
            return

        await state.update_data(function=function)
        await message.answer("Введите вашу <b>категорию</b> (например 1 категория, 2 и тд):", parse_mode=ParseMode.HTML)
        await RegisterReferee.next()
        logger.info("Register FSM: function accepted: %r (user_id=%s)", function, message.from_user.id)

    except Exception as e:
        logger.exception("process_function failed (user_id=%s): %s", getattr(message.from_user, "id", None), e)
        await message.answer("⚠️ Произошла ошибка при обработке функции. Повторите ввод, пожалуйста.")


async def process_category(message: types.Message, state: FSMContext):
    """
    Шаг FSM: ввод категории
    - Проверяем текст
    - Безопасно читаем FSM-данные
    - Безопасный commit() с обработкой IntegrityError
    """
    if not getattr(message, "text", None):
        await message.answer("❌ Пожалуйста, отправьте текст с вашей категорией.")
        return

    category = (message.text or "").strip()
    category = re.sub(r"\s+", " ", category)
    if not category:
        await message.answer("❌ Поле не может быть пустым. Введите вашу категорию:")
        return

    data = await state.get_data()
    # Проверим, что предыдущие шаги есть
    required_keys = ("first_name", "last_name", "function")
    if not all(k in data and data[k] for k in required_keys):
        # Пользователь сбил FSM – начнём регистрацию заново
        await message.answer("⚠️ Сессия регистрации сбилась. Давайте начнём заново: /start")
        await state.finish()
        return

    session = SessionLocal()
    try:
        user_in_db = session.query(User).filter(User.user_id == message.from_user.id).first()
        if not user_in_db:
            user_in_db = User(
                user_id=message.from_user.id,
                first_name=data['first_name'],
                last_name=data['last_name'],
                function=data['function'],
                category=category
            )
            session.add(user_in_db)
        else:
            # если вдруг повторная регистрация — мягко обновим профиль
            user_in_db.first_name = data['first_name']
            user_in_db.last_name  = data['last_name']
            user_in_db.function   = data['function']
            user_in_db.category   = category

        try:
            session.commit()
        except IntegrityError as ie:
            session.rollback()
            logger.error("IntegrityError on user commit (user_id=%s): %s", message.from_user.id, ie)
            await message.answer("⚠️ Некорректные данные пользователя. Проверьте введённые поля и попробуйте ещё раз.")
            return

        logger.info(
            "Register FSM: user saved (user_id=%s, %s %s, function=%s, category=%s)",
            message.from_user.id, user_in_db.first_name, user_in_db.last_name, user_in_db.function, user_in_db.category
        )
        # Завершаем FSM сессию
        from utils.fsm_guard import get_fsm_guard
        fsm_guard = get_fsm_guard()
        fsm_guard.end_session(message.from_user.id)
        
        # Устанавливаем контекст пользователя как обычный пользователь
        from utils.menu_manager import get_menu_manager
        menu_manager = get_menu_manager()
        menu_manager.set_user_context(message.from_user.id, "user")
        await message.answer("✅ Вы успешно зарегистрированы! 🎉", reply_markup=main_menu())

    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Ошибка при регистрации пользователя {message.from_user.id}: {e}")
        await message.answer("❌ Произошла ошибка при регистрации. Попробуйте позже.")
    finally:
        session.close()
        await state.finish()


async def process_cancel_payment_input(callback_query: types.CallbackQuery, state: FSMContext):
    """Отмена ввода суммы оплаты"""
    try:
        # Завершаем FSM сессию
        from utils.fsm_guard import get_fsm_guard
        fsm_guard = get_fsm_guard()
        fsm_guard.end_session(callback_query.from_user.id)
        
        await state.finish()
        
        await callback_query.message.answer(
            "❌ <b>Ввод суммы отменен</b>\n\n"
            "Вы можете вернуться к этому позже через меню заработка.",
            parse_mode=ParseMode.HTML
        )
        
        # Возвращаем в главное меню
        from utils.menu_manager import get_menu_manager
        menu_manager = get_menu_manager()
        await menu_manager.return_to_menu(callback_query, state)
        
    except Exception as e:
        logger.error(f"Ошибка при отмене ввода суммы оплаты: {e}")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте позже.")
    finally:
        await callback_query.answer()

async def process_back_to_main(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработка кнопки 'Назад в главное меню'"""
    try:
        # Завершаем FSM сессию если она активна
        from utils.fsm_guard import get_fsm_guard
        fsm_guard = get_fsm_guard()
        fsm_guard.end_session(callback_query.from_user.id)
        
        # Завершаем FSM состояние
        await state.finish()
        
        # Возвращаем в главное меню
        from utils.menu_manager import get_menu_manager
        menu_manager = get_menu_manager()
        await menu_manager.return_to_menu(callback_query, state)
        
    except Exception as e:
        logger.error(f"Ошибка при возврате в главное меню: {e}")
        # Fallback - просто отправляем главное меню
        from keyboards import main_menu
        await callback_query.message.answer("🏆 Главное меню:", reply_markup=main_menu())
    finally:
        await callback_query.answer()
    """
    Обработка кнопки "Назад" в главном меню
    """
    from utils.menu_manager import get_menu_manager
    menu_manager = get_menu_manager()
    await menu_manager.handle_back_button(callback_query, state)
