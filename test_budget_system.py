# test_budget_system.py
"""
Тестовый скрипт для проверки системы бюджетирования турниров
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Импорты для работы с базой данных
from database import SessionLocal
from models import Tournament, TournamentBudget, User, Registration, RegistrationStatus, JudgePayment
from services.budget_service import BudgetService

class MockBot:
    """Мок-бот для тестирования"""
    
    def __init__(self):
        self.sent_messages = []
    
    async def send_message(self, chat_id, text, reply_markup=None, parse_mode=None):
        """Мок-метод для отправки сообщений"""
        message_data = {
            'chat_id': chat_id,
            'text': text,
            'reply_markup': reply_markup,
            'parse_mode': parse_mode,
            'timestamp': datetime.now()
        }
        self.sent_messages.append(message_data)
        print(f"📤 ОТПРАВЛЕНО СООБЩЕНИЕ:")
        print(f"   Чат ID: {chat_id}")
        print(f"   Текст: {text}")
        if reply_markup:
            print(f"   Клавиатура: {len(reply_markup.inline_keyboard)} кнопок")
        print(f"   Время: {message_data['timestamp'].strftime('%H:%M:%S')}")
        print("-" * 50)

async def create_test_data():
    """Создает тестовые данные для проверки"""
    session = SessionLocal()
    try:
        print("🔧 Создание тестовых данных...")
        
        # Создаем тестового пользователя
        test_user = session.query(User).filter(User.user_id == 999999).first()
        if not test_user:
            test_user = User(
                user_id=999999,
                first_name="Тест",
                last_name="Пользователь",
                function="Судья",
                category="1 категория"
            )
            session.add(test_user)
            print("✅ Создан тестовый пользователь")
        
        # Создаем тестовые турниры
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        # Турнир на завтра (для тестирования напоминаний)
        test_tournament1 = session.query(Tournament).filter(
            Tournament.name == "Тестовый турнир 1"
        ).first()
        if not test_tournament1:
            test_tournament1 = Tournament(
                name="Тестовый турнир 1",
                date=tomorrow
            )
            session.add(test_tournament1)
            print("✅ Создан тестовый турнир 1 на завтра")
        
        # Турнир на послезавтра
        day_after_tomorrow = today + timedelta(days=2)
        test_tournament2 = session.query(Tournament).filter(
            Tournament.name == "Тестовый турнир 2"
        ).first()
        if not test_tournament2:
            test_tournament2 = Tournament(
                name="Тестовый турнир 2",
                date=day_after_tomorrow
            )
            session.add(test_tournament2)
            print("✅ Создан тестовый турнир 2 на послезавтра")
        
        # Турнир на сегодня (для тестирования множественных турниров)
        test_tournament3 = session.query(Tournament).filter(
            Tournament.name == "Тестовый турнир 3"
        ).first()
        if not test_tournament3:
            test_tournament3 = Tournament(
                name="Тестовый турнир 3",
                date=tomorrow
            )
            session.add(test_tournament3)
            print("✅ Создан тестовый турнир 3 на завтра")
        
        # Турнир на сегодня (для тестирования множественных турниров)
        test_tournament4 = session.query(Tournament).filter(
            Tournament.name == "Тестовый турнир 4"
        ).first()
        if not test_tournament4:
            test_tournament4 = Tournament(
                name="Тестовый турнир 4",
                date=tomorrow
            )
            session.add(test_tournament4)
            print("✅ Создан тестовый турнир 4 на завтра")
        
        # Турнир на сегодня (для тестирования множественных турниров)
        test_tournament5 = session.query(Tournament).filter(
            Tournament.name == "Тестовый турнир 5"
        ).first()
        if not test_tournament5:
            test_tournament5 = Tournament(
                name="Тестовый турнир 5",
                date=tomorrow
            )
            session.add(test_tournament5)
            print("✅ Создан тестовый турнир 5 на завтра")
        
        session.commit()
        print("✅ Все тестовые данные созданы")
        
        return {
            'user': test_user,
            'tournament1': test_tournament1,
            'tournament2': test_tournament2,
            'tournament3': test_tournament3,
            'tournament4': test_tournament4,
            'tournament5': test_tournament5
        }
        
    except Exception as e:
        logger.error(f"Ошибка при создании тестовых данных: {e}")
        session.rollback()
        return None
    finally:
        session.close()

async def test_budget_reminders():
    """Тестирует отправку напоминаний о бюджете"""
    print("\n🧪 ТЕСТ 1: Отправка напоминаний о бюджете")
    print("=" * 60)
    
    # Создаем мок-бот
    mock_bot = MockBot()
    
    # Создаем сервис бюджета
    budget_service = BudgetService(mock_bot)
    
    # Отправляем напоминания
    reminders_sent = await budget_service.send_budget_reminders()
    
    print(f"📊 Результат: отправлено {reminders_sent} напоминаний")
    print(f"📱 Сообщений в мок-боте: {len(mock_bot.sent_messages)}")
    
    return mock_bot.sent_messages

async def test_budget_setting():
    """Тестирует установку бюджета"""
    print("\n🧪 ТЕСТ 2: Установка бюджета турнира")
    print("=" * 60)
    
    session = SessionLocal()
    try:
        # Находим тестовый турнир
        tournament = session.query(Tournament).filter(
            Tournament.name == "Тестовый турнир 1"
        ).first()
        
        if not tournament:
            print("❌ Тестовый турнир не найден")
            return False
        
        # Создаем сервис бюджета
        budget_service = BudgetService()
        
        # Устанавливаем бюджет
        budget_amount = 10000.0
        success = await budget_service.set_tournament_budget(tournament.tournament_id, budget_amount)
        
        if success:
            print(f"✅ Бюджет {budget_amount} руб. установлен для турнира '{tournament.name}'")
            
            # Проверяем, что бюджет сохранился
            budget_info = await budget_service.get_tournament_budget(tournament.tournament_id)
            if budget_info:
                print(f"📊 Информация о бюджете:")
                print(f"   • Общий бюджет: {budget_info['total_budget']:,.0f} руб.")
                print(f"   • Выплачено судьям: {budget_info['judges_payment']:,.0f} руб.")
                print(f"   • Прибыль админа: {budget_info['admin_profit']:,.0f} руб.")
                print(f"   • Дата установки: {budget_info['budget_set_date']}")
            else:
                print("❌ Не удалось получить информацию о бюджете")
                return False
        else:
            print("❌ Не удалось установить бюджет")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при тестировании установки бюджета: {e}")
        return False
    finally:
        session.close()

async def test_judges_payment():
    """Тестирует выплаты судьям и пересчет прибыли"""
    print("\n🧪 ТЕСТ 3: Выплаты судьям и пересчет прибыли")
    print("=" * 60)
    
    session = SessionLocal()
    try:
        # Находим тестовый турнир
        tournament = session.query(Tournament).filter(
            Tournament.name == "Тестовый турнир 1"
        ).first()
        
        if not tournament:
            print("❌ Тестовый турнир не найден")
            return False
        
        # Находим тестового пользователя
        user = session.query(User).filter(User.user_id == 999999).first()
        
        if not user:
            print("❌ Тестовый пользователь не найден")
            return False
        
        # Создаем запись о выплате судье
        payment = JudgePayment(
            user_id=user.user_id,
            tournament_id=tournament.tournament_id,
            amount=1500.0,
            is_paid=True,
            payment_date=datetime.now()
        )
        session.add(payment)
        session.commit()
        
        print(f"✅ Создана запись о выплате {payment.amount} руб. судье {user.first_name} {user.last_name}")
        
        # Обновляем выплаты в бюджете
        budget_service = BudgetService()
        await budget_service.update_judges_payment(tournament.tournament_id)
        
        # Проверяем обновленную информацию о бюджете
        budget_info = await budget_service.get_tournament_budget(tournament.tournament_id)
        if budget_info:
            print(f"📊 Обновленная информация о бюджете:")
            print(f"   • Общий бюджет: {budget_info['total_budget']:,.0f} руб.")
            print(f"   • Выплачено судьям: {budget_info['judges_payment']:,.0f} руб.")
            print(f"   • Прибыль админа: {budget_info['admin_profit']:,.0f} руб.")
            print(f"   • Рентабельность: {(budget_info['admin_profit'] / budget_info['total_budget'] * 100):.1f}%")
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при тестировании выплат судьям: {e}")
        session.rollback()
        return False
    finally:
        session.close()

async def test_admin_profit_summary():
    """Тестирует сводку по прибыли админа"""
    print("\n🧪 ТЕСТ 4: Сводка по прибыли админа")
    print("=" * 60)
    
    try:
        budget_service = BudgetService()
        profit_summary = await budget_service.get_admin_profit_summary()
        
        print(f"📊 Сводка по прибыли админа:")
        print(f"   • Общая прибыль: {profit_summary['total_profit']:,.0f} руб.")
        print(f"   • Прибыль за месяц: {profit_summary['monthly_profit']:,.0f} руб.")
        print(f"   • Прибыль за сезон: {profit_summary['seasonal_profit']:,.0f} руб.")
        print(f"   • Турниров с прибылью: {profit_summary['tournaments_count']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при тестировании сводки по прибыли: {e}")
        return False

async def test_all_budgets():
    """Тестирует получение всех бюджетов"""
    print("\n🧪 ТЕСТ 5: Получение всех бюджетов")
    print("=" * 60)
    
    try:
        budget_service = BudgetService()
        budgets = await budget_service.get_all_budgets()
        
        print(f"📊 Найдено бюджетов: {len(budgets)}")
        
        for budget in budgets:
            print(f"   • {budget['tournament_name']} ({budget['tournament_date'].strftime('%d.%m.%Y')})")
            print(f"     Бюджет: {budget['total_budget']:,.0f} руб.")
            print(f"     Судьям: {budget['judges_payment']:,.0f} руб.")
            print(f"     Прибыль: {budget['admin_profit']:,.0f} руб.")
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при тестировании получения всех бюджетов: {e}")
        return False

async def cleanup_test_data():
    """Очищает тестовые данные"""
    print("\n🧹 Очистка тестовых данных...")
    
    session = SessionLocal()
    try:
        # Удаляем тестовые записи
        session.query(JudgePayment).filter(JudgePayment.user_id == 999999).delete()
        session.query(TournamentBudget).filter(
            TournamentBudget.tournament_id.in_(
                session.query(Tournament.tournament_id).filter(
                    Tournament.name.like("Тестовый турнир%")
                )
            )
        ).delete()
        session.query(Tournament).filter(Tournament.name.like("Тестовый турнир%")).delete()
        session.query(User).filter(User.user_id == 999999).delete()
        
        session.commit()
        print("✅ Тестовые данные очищены")
        
    except Exception as e:
        logger.error(f"Ошибка при очистке тестовых данных: {e}")
        session.rollback()
    finally:
        session.close()

async def main():
    """Основная функция тестирования"""
    print("🚀 ЗАПУСК ТЕСТИРОВАНИЯ СИСТЕМЫ БЮДЖЕТИРОВАНИЯ")
    print("=" * 60)
    
    # Создаем тестовые данные
    test_data = await create_test_data()
    if not test_data:
        print("❌ Не удалось создать тестовые данные")
        return
    
    print("\n" + "=" * 60)
    
    # Запускаем тесты
    tests = [
        ("Напоминания о бюджете", test_budget_reminders),
        ("Установка бюджета", test_budget_setting),
        ("Выплаты судьям", test_judges_payment),
        ("Сводка по прибыли", test_admin_profit_summary),
        ("Все бюджеты", test_all_budgets)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Ошибка в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    # Выводим результаты
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Итого: {passed}/{len(results)} тестов пройдено")
    
    if passed == len(results):
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        print("⚠️ Некоторые тесты провалены. Проверьте логи выше.")
    
    # Очищаем тестовые данные
    await cleanup_test_data()
    
    print("\n🏁 Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(main())
