# manual_budget_test.py
"""
Ручной тест системы бюджетирования для админа
Позволяет проверить напоминания и установку бюджетов
"""

import asyncio
import logging
from datetime import datetime, date, timedelta

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from database import SessionLocal
from models import Tournament, TournamentBudget
from services.budget_service import BudgetService

class TestBot:
    """Тестовый бот для демонстрации"""
    
    def __init__(self):
        self.admin_id = 453424504  # Ваш ID
    
    async def send_message(self, chat_id, text, reply_markup=None, parse_mode=None):
        """Отправляет сообщение (в реальности - в консоль)"""
        print("\n" + "="*60)
        print("📱 СООБЩЕНИЕ ДЛЯ АДМИНА:")
        print("="*60)
        print(f"👤 Получатель: {chat_id}")
        print(f"📝 Текст:\n{text}")
        
        if reply_markup and hasattr(reply_markup, 'inline_keyboard'):
            print(f"\n🔘 Кнопки ({len(reply_markup.inline_keyboard)} строк):")
            for i, row in enumerate(reply_markup.inline_keyboard, 1):
                print(f"   Строка {i}:")
                for button in row:
                    print(f"     • {button.text} (callback: {button.callback_data})")
        
        print("="*60)
        return True

async def create_test_tournaments():
    """Создает тестовые турниры для проверки"""
    session = SessionLocal()
    try:
        print("🔧 Создание тестовых турниров...")
        
        # Удаляем старые тестовые турниры
        session.query(Tournament).filter(Tournament.name.like("Тест%")).delete()
        session.query(TournamentBudget).filter(
            TournamentBudget.tournament_id.in_(
                session.query(Tournament.tournament_id).filter(
                    Tournament.name.like("Тест%")
                )
            )
        ).delete()
        session.commit()
        
        # Создаем турниры на завтра
        tomorrow = date.today() + timedelta(days=1)
        
        tournaments = [
            "Тест - Новогодний турнир",
            "Тест - Рождественский турнир", 
            "Тест - Зимний турнир",
            "Тест - Снежный турнир",
            "Тест - Морозный турнир"
        ]
        
        created_tournaments = []
        for name in tournaments:
            tournament = Tournament(
                name=name, 
                date=tomorrow,
                month=tomorrow.strftime('%B')
            )
            session.add(tournament)
            created_tournaments.append(tournament)
        
        session.commit()
        
        print(f"✅ Создано {len(created_tournaments)} тестовых турниров на {tomorrow.strftime('%d.%m.%Y')}")
        
        return created_tournaments
        
    except Exception as e:
        logger.error(f"Ошибка при создании тестовых турниров: {e}")
        session.rollback()
        return []
    finally:
        session.close()

async def test_single_tournament_reminder():
    """Тестирует напоминание для одного турнира"""
    print("\n🧪 ТЕСТ 1: Напоминание для одного турнира")
    print("="*50)
    
        # Создаем один турнир
        session = SessionLocal()
        try:
            tomorrow = date.today() + timedelta(days=1)
            tournament = Tournament(
                name="Тест - Одиночный турнир", 
                date=tomorrow,
                month=tomorrow.strftime('%B')
            )
            session.add(tournament)
            session.commit()
        
        # Создаем сервис с тестовым ботом
        test_bot = TestBot()
        budget_service = BudgetService(test_bot)
        
        # Отправляем напоминание
        await budget_service.send_budget_reminders()
        
    except Exception as e:
        logger.error(f"Ошибка в тесте одиночного турнира: {e}")
    finally:
        session.close()

async def test_multiple_tournaments_reminder():
    """Тестирует напоминание для нескольких турниров"""
    print("\n🧪 ТЕСТ 2: Напоминание для нескольких турниров")
    print("="*50)
    
    # Создаем несколько турниров
    tournaments = await create_test_tournaments()
    
    if not tournaments:
        print("❌ Не удалось создать тестовые турниры")
        return
    
    # Создаем сервис с тестовым ботом
    test_bot = TestBot()
    budget_service = BudgetService(test_bot)
    
    # Отправляем напоминание
    await budget_service.send_budget_reminders()

async def test_budget_setting():
    """Тестирует установку бюджета"""
    print("\n🧪 ТЕСТ 3: Установка бюджета")
    print("="*50)
    
    session = SessionLocal()
    try:
        # Находим тестовый турнир
        tournament = session.query(Tournament).filter(
            Tournament.name == "Тест - Одиночный турнир"
        ).first()
        
        if not tournament:
            print("❌ Тестовый турнир не найден")
            return
        
        # Создаем сервис
        budget_service = BudgetService()
        
        # Устанавливаем бюджет
        budget_amount = 15000.0
        success = await budget_service.set_tournament_budget(tournament.tournament_id, budget_amount)
        
        if success:
            print(f"✅ Бюджет {budget_amount:,.0f} руб. установлен для турнира '{tournament.name}'")
            
            # Показываем информацию о бюджете
            budget_info = await budget_service.get_tournament_budget(tournament.tournament_id)
            if budget_info:
                print(f"\n📊 Информация о бюджете:")
                print(f"   • Общий бюджет: {budget_info['total_budget']:,.0f} руб.")
                print(f"   • Выплачено судьям: {budget_info['judges_payment']:,.0f} руб.")
                print(f"   • Прибыль админа: {budget_info['admin_profit']:,.0f} руб.")
                print(f"   • Дата установки: {budget_info['budget_set_date'].strftime('%d.%m.%Y %H:%M')}")
        else:
            print("❌ Не удалось установить бюджет")
            
    except Exception as e:
        logger.error(f"Ошибка при установке бюджета: {e}")
    finally:
        session.close()

async def test_admin_profit():
    """Тестирует дашборд прибыли админа"""
    print("\n🧪 ТЕСТ 4: Дашборд прибыли админа")
    print("="*50)
    
    try:
        budget_service = BudgetService()
        profit_summary = await budget_service.get_admin_profit_summary()
        
        print("📊 ДАШБОРД ПРИБЫЛИ АДМИНА:")
        print(f"   💰 Общая прибыль: {profit_summary['total_profit']:,.0f} руб.")
        print(f"   📅 За месяц: {profit_summary['monthly_profit']:,.0f} руб.")
        print(f"   🎓 За сезон: {profit_summary['seasonal_profit']:,.0f} руб.")
        print(f"   🏆 Турниров с прибылью: {profit_summary['tournaments_count']}")
        
        if profit_summary['tournaments_count'] > 0:
            avg_profit = profit_summary['total_profit'] / profit_summary['tournaments_count']
            print(f"   📊 Средняя прибыль за турнир: {avg_profit:,.0f} руб.")
        
    except Exception as e:
        logger.error(f"Ошибка при получении дашборда прибыли: {e}")

async def test_all_budgets():
    """Тестирует просмотр всех бюджетов"""
    print("\n🧪 ТЕСТ 5: Просмотр всех бюджетов")
    print("="*50)
    
    try:
        budget_service = BudgetService()
        budgets = await budget_service.get_all_budgets()
        
        if not budgets:
            print("📊 Нет установленных бюджетов")
            return
        
        print(f"📊 ВСЕ БЮДЖЕТЫ ТУРНИРОВ ({len(budgets)} шт.):")
        print("-" * 50)
        
        total_budget = 0
        total_judges_payment = 0
        total_admin_profit = 0
        
        for budget in budgets:
            print(f"🏆 {budget['tournament_name']}")
            print(f"   📅 {budget['tournament_date'].strftime('%d.%m.%Y')}")
            print(f"   💰 Бюджет: {budget['total_budget']:,.0f} руб.")
            print(f"   👥 Судьям: {budget['judges_payment']:,.0f} руб.")
            print(f"   💼 Прибыль: {budget['admin_profit']:,.0f} руб.")
            
            if budget['total_budget'] > 0:
                profitability = (budget['admin_profit'] / budget['total_budget']) * 100
                print(f"   📈 Рентабельность: {profitability:.1f}%")
            
            print()
            
            total_budget += budget['total_budget']
            total_judges_payment += budget['judges_payment']
            total_admin_profit += budget['admin_profit']
        
        print("=" * 50)
        print(f"📈 ИТОГО:")
        print(f"   💰 Общий бюджет: {total_budget:,.0f} руб.")
        print(f"   👥 Выплачено судьям: {total_judges_payment:,.0f} руб.")
        print(f"   💼 Общая прибыль: {total_admin_profit:,.0f} руб.")
        
        if total_budget > 0:
            avg_profitability = (total_admin_profit / total_budget) * 100
            print(f"   📊 Средняя рентабельность: {avg_profitability:.1f}%")
        
    except Exception as e:
        logger.error(f"Ошибка при получении всех бюджетов: {e}")

async def cleanup_test_data():
    """Очищает тестовые данные"""
    print("\n🧹 Очистка тестовых данных...")
    
    session = SessionLocal()
    try:
        # Удаляем тестовые записи
        session.query(TournamentBudget).filter(
            TournamentBudget.tournament_id.in_(
                session.query(Tournament.tournament_id).filter(
                    Tournament.name.like("Тест%")
                )
            )
        ).delete()
        session.query(Tournament).filter(Tournament.name.like("Тест%")).delete()
        session.commit()
        print("✅ Тестовые данные очищены")
        
    except Exception as e:
        logger.error(f"Ошибка при очистке: {e}")
        session.rollback()
    finally:
        session.close()

async def interactive_test():
    """Интерактивное тестирование"""
    print("🚀 ИНТЕРАКТИВНОЕ ТЕСТИРОВАНИЕ СИСТЕМЫ БЮДЖЕТИРОВАНИЯ")
    print("="*60)
    
    while True:
        print("\n📋 ВЫБЕРИТЕ ТЕСТ:")
        print("1. Напоминание для одного турнира")
        print("2. Напоминание для нескольких турниров")
        print("3. Установка бюджета")
        print("4. Дашборд прибыли админа")
        print("5. Просмотр всех бюджетов")
        print("6. Очистить тестовые данные")
        print("0. Выход")
        
        choice = input("\nВведите номер теста (0-6): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            await test_single_tournament_reminder()
        elif choice == "2":
            await test_multiple_tournaments_reminder()
        elif choice == "3":
            await test_budget_setting()
        elif choice == "4":
            await test_admin_profit()
        elif choice == "5":
            await test_all_budgets()
        elif choice == "6":
            await cleanup_test_data()
        else:
            print("❌ Неверный выбор. Попробуйте снова.")
        
        input("\nНажмите Enter для продолжения...")

if __name__ == "__main__":
    asyncio.run(interactive_test())
