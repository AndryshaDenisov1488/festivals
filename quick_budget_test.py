# quick_budget_test.py
"""
Быстрый тест системы бюджетирования
Создает тестовые турниры и показывает, как работают напоминания
"""

import asyncio
from datetime import date, timedelta
from database import SessionLocal
from models import Tournament
from services.budget_service import BudgetService

class QuickTestBot:
    """Быстрый тестовый бот"""
    
    async def send_message(self, chat_id, text, reply_markup=None, parse_mode=None):
        print("\n" + "🔔" * 20)
        print("НАПОМИНАНИЕ О БЮДЖЕТЕ:")
        print("🔔" * 20)
        print(text)
        
        if reply_markup and hasattr(reply_markup, 'inline_keyboard'):
            print("\n🔘 ДОСТУПНЫЕ ДЕЙСТВИЯ:")
            for i, row in enumerate(reply_markup.inline_keyboard, 1):
                for button in row:
                    print(f"   {i}. {button.text}")
        print("🔔" * 20)

async def main():
    print("🚀 БЫСТРЫЙ ТЕСТ СИСТЕМЫ БЮДЖЕТИРОВАНИЯ")
    print("="*50)
    
    # Создаем тестовые турниры
    session = SessionLocal()
    try:
        # Очищаем старые тесты
        from models import TournamentBudget
        session.query(TournamentBudget).filter(
            TournamentBudget.tournament_id.in_(
                session.query(Tournament.tournament_id).filter(
                    Tournament.name.like("Быстрый тест%")
                )
            )
        ).delete()
        session.query(Tournament).filter(Tournament.name.like("Быстрый тест%")).delete()
        session.commit()
        
        # Создаем турниры на завтра
        tomorrow = date.today() + timedelta(days=1)
        
        tournaments = [
            "Быстрый тест - Турнир 1",
            "Быстрый тест - Турнир 2", 
            "Быстрый тест - Турнир 3"
        ]
        
        for name in tournaments:
            tournament = Tournament(
                name=name, 
                date=tomorrow,
                month=tomorrow.strftime('%B')  # Добавляем месяц
            )
            session.add(tournament)
        
        session.commit()
        print(f"✅ Создано {len(tournaments)} тестовых турниров на {tomorrow.strftime('%d.%m.%Y')}")
        
    except Exception as e:
        print(f"❌ Ошибка при создании турниров: {e}")
        return
    finally:
        session.close()
    
    # Тестируем напоминания
    print("\n🧪 Тестирование напоминаний...")
    
    test_bot = QuickTestBot()
    budget_service = BudgetService(test_bot)
    
    # Отправляем напоминания
    reminders_sent = await budget_service.send_budget_reminders()
    
    print(f"\n📊 Результат: отправлено {reminders_sent} напоминаний")
    
    # Тестируем установку бюджета
    print("\n🧪 Тестирование установки бюджета...")
    
    session = SessionLocal()
    try:
        tournament = session.query(Tournament).filter(
            Tournament.name == "Быстрый тест - Турнир 1"
        ).first()
        
        if tournament:
            # Устанавливаем бюджет
            success = await budget_service.set_tournament_budget(tournament.tournament_id, 5000.0)
            
            if success:
                print("✅ Бюджет 5,000 руб. установлен успешно")
                
                # Показываем информацию о бюджете
                budget_info = await budget_service.get_tournament_budget(tournament.tournament_id)
                if budget_info:
                    print(f"\n📊 Информация о бюджете:")
                    print(f"   💰 Общий бюджет: {budget_info['total_budget']:,.0f} руб.")
                    print(f"   👥 Выплачено судьям: {budget_info['judges_payment']:,.0f} руб.")
                    print(f"   💼 Прибыль админа: {budget_info['admin_profit']:,.0f} руб.")
            else:
                print("❌ Не удалось установить бюджет")
        
    except Exception as e:
        print(f"❌ Ошибка при установке бюджета: {e}")
    finally:
        session.close()
    
    # Показываем сводку по прибыли
    print("\n🧪 Тестирование сводки по прибыли...")
    
    try:
        profit_summary = await budget_service.get_admin_profit_summary()
        
        print(f"\n📊 СВОДКА ПО ПРИБЫЛИ:")
        print(f"   💰 Общая прибыль: {profit_summary['total_profit']:,.0f} руб.")
        print(f"   📅 За месяц: {profit_summary['monthly_profit']:,.0f} руб.")
        print(f"   🎓 За сезон: {profit_summary['seasonal_profit']:,.0f} руб.")
        print(f"   🏆 Турниров с прибылью: {profit_summary['tournaments_count']}")
        
    except Exception as e:
        print(f"❌ Ошибка при получении сводки: {e}")
    
    # Очищаем тестовые данные
    print("\n🧹 Очистка тестовых данных...")
    
    session = SessionLocal()
    try:
        from models import TournamentBudget
        session.query(TournamentBudget).filter(
            TournamentBudget.tournament_id.in_(
                session.query(Tournament.tournament_id).filter(
                    Tournament.name.like("Быстрый тест%")
                )
            )
        ).delete()
        session.query(Tournament).filter(Tournament.name.like("Быстрый тест%")).delete()
        session.commit()
        print("✅ Тестовые данные очищены")
        
    except Exception as e:
        print(f"❌ Ошибка при очистке: {e}")
    finally:
        session.close()
    
    print("\n🎉 Тестирование завершено!")
    print("💡 Для полного тестирования запустите: python manual_budget_test.py")

if __name__ == "__main__":
    asyncio.run(main())
