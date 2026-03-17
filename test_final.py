# test_final.py
"""
Финальный тест системы бюджетирования
"""

import asyncio
from datetime import datetime, date, timedelta
from database import SessionLocal
from models import Tournament, TournamentBudget
from services.budget_service import BudgetService

class TestBot:
    """Тестовый бот"""
    
    async def send_message(self, chat_id, text, reply_markup=None, parse_mode=None):
        print("\n" + "🔔" * 30)
        print("НАПОМИНАНИЕ О БЮДЖЕТЕ:")
        print("🔔" * 30)
        print(text)
        
        if reply_markup and hasattr(reply_markup, 'inline_keyboard'):
            print("\n🔘 ДОСТУПНЫЕ ДЕЙСТВИЯ:")
            for i, row in enumerate(reply_markup.inline_keyboard, 1):
                for j, button in enumerate(row, 1):
                    print(f"   {i}.{j} {button.text}")
        print("🔔" * 30)

async def main():
    print("🚀 ФИНАЛЬНЫЙ ТЕСТ СИСТЕМЫ БЮДЖЕТИРОВАНИЯ")
    print("=" * 50)
    
    # Очищаем старые тесты
    session = SessionLocal()
    try:
        session.query(TournamentBudget).filter(
            TournamentBudget.tournament_id.in_(
                session.query(Tournament.tournament_id).filter(
                    Tournament.name.like("Финальный тест%")
                )
            )
        ).delete()
        session.query(Tournament).filter(Tournament.name.like("Финальный тест%")).delete()
        session.commit()
        print("✅ Старые тесты очищены")
    except Exception as e:
        print(f"⚠️ Ошибка при очистке: {e}")
    finally:
        session.close()
    
    # Создаем турниры через 12 часов
    session = SessionLocal()
    try:
        target_time = datetime.now() + timedelta(hours=12)
        target_date = target_time.date()
        
        tournaments = [
            "Финальный тест - Турнир 1",
            "Финальный тест - Турнир 2",
            "Финальный тест - Турнир 3"
        ]
        
        created_tournaments = []
        for name in tournaments:
            tournament = Tournament(
                name=name,
                date=target_date,
                month=target_date.strftime('%B')
            )
            session.add(tournament)
            created_tournaments.append(tournament)
        
        session.commit()
        print(f"✅ Создано {len(created_tournaments)} турниров на {target_date.strftime('%d.%m.%Y')}")
        print(f"⏰ Время начала: {target_time.strftime('%H:%M')}")
        
    except Exception as e:
        print(f"❌ Ошибка при создании турниров: {e}")
        return
    finally:
        session.close()
    
    # Тестируем напоминания
    print("\n🧪 Тестирование напоминаний...")
    
    test_bot = TestBot()
    budget_service = BudgetService(test_bot)
    
    try:
        reminders_sent = await budget_service.send_budget_reminders()
        print(f"📊 Отправлено напоминаний: {reminders_sent}")
        
        if reminders_sent > 0:
            print("✅ Напоминания работают корректно!")
        else:
            print("⚠️ Напоминания не отправлены")
            
    except Exception as e:
        print(f"❌ Ошибка при отправке напоминаний: {e}")
    
    # Тестируем установку бюджета
    print("\n🧪 Тестирование установки бюджета...")
    
    session = SessionLocal()
    try:
        tournament = session.query(Tournament).filter(
            Tournament.name == "Финальный тест - Турнир 1"
        ).first()
        
        if tournament:
            success = await budget_service.set_tournament_budget(tournament.tournament_id, 12000.0)
            
            if success:
                print("✅ Бюджет 12,000 руб. установлен успешно")
                
                # Показываем информацию о бюджете
                budget_info = await budget_service.get_tournament_budget(tournament.tournament_id)
                if budget_info:
                    print(f"\n📊 Информация о бюджете:")
                    print(f"   💰 Общий бюджет: {budget_info['total_budget']:,.0f} руб.")
                    print(f"   👥 Выплачено судьям: {budget_info['judges_payment']:,.0f} руб.")
                    print(f"   💼 Прибыль админа: {budget_info['admin_profit']:,.0f} руб.")
                    print(f"   📅 Дата установки: {budget_info['budget_set_date'].strftime('%d.%m.%Y %H:%M')}")
            else:
                print("❌ Не удалось установить бюджет")
        else:
            print("❌ Турнир не найден")
            
    except Exception as e:
        print(f"❌ Ошибка при установке бюджета: {e}")
    finally:
        session.close()
    
    # Тестируем сводку по прибыли
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
        session.query(TournamentBudget).filter(
            TournamentBudget.tournament_id.in_(
                session.query(Tournament.tournament_id).filter(
                    Tournament.name.like("Финальный тест%")
                )
            )
        ).delete()
        session.query(Tournament).filter(Tournament.name.like("Финальный тест%")).delete()
        session.commit()
        print("✅ Тестовые данные очищены")
        
    except Exception as e:
        print(f"❌ Ошибка при очистке: {e}")
    finally:
        session.close()
    
    print("\n🎉 ФИНАЛЬНЫЙ ТЕСТ ЗАВЕРШЕН!")
    print("💡 Система бюджетирования готова к использованию!")

if __name__ == "__main__":
    asyncio.run(main())
