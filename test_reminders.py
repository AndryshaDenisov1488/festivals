# test_reminders.py
"""
Тест напоминаний о бюджете
Создает турниры, которые начинаются через 12 часов
"""

import asyncio
from datetime import datetime, date, timedelta
from database import SessionLocal
from models import Tournament, TournamentBudget
from services.budget_service import BudgetService

class TestBot:
    """Тестовый бот для демонстрации напоминаний"""
    
    async def send_message(self, chat_id, text, reply_markup=None, parse_mode=None):
        print("\n" + "🔔" * 30)
        print("НАПОМИНАНИЕ О БЮДЖЕТЕ ТУРНИРА:")
        print("🔔" * 30)
        print(text)
        
        if reply_markup and hasattr(reply_markup, 'inline_keyboard'):
            print("\n🔘 ДОСТУПНЫЕ ДЕЙСТВИЯ:")
            for i, row in enumerate(reply_markup.inline_keyboard, 1):
                for j, button in enumerate(row, 1):
                    print(f"   {i}.{j} {button.text}")
        print("🔔" * 30)

async def create_tournaments_for_reminders():
    """Создает турниры, которые начинаются через 12 часов"""
    session = SessionLocal()
    try:
        # Очищаем старые тесты
        session.query(TournamentBudget).filter(
            TournamentBudget.tournament_id.in_(
                session.query(Tournament.tournament_id).filter(
                    Tournament.name.like("Тест напоминаний%")
                )
            )
        ).delete()
        session.query(Tournament).filter(Tournament.name.like("Тест напоминаний%")).delete()
        session.commit()
        
        # Создаем турниры через 12 часов
        target_time = datetime.now() + timedelta(hours=12)
        target_date = target_time.date()
        
        tournaments = [
            "Тест напоминаний - Одиночный турнир",
            "Тест напоминаний - Турнир 1",
            "Тест напоминаний - Турнир 2", 
            "Тест напоминаний - Турнир 3",
            "Тест напоминаний - Турнир 4"
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
        
        print(f"✅ Создано {len(created_tournaments)} тестовых турниров на {target_date.strftime('%d.%m.%Y')}")
        print(f"⏰ Время начала: {target_time.strftime('%H:%M')}")
        
        return created_tournaments
        
    except Exception as e:
        print(f"❌ Ошибка при создании турниров: {e}")
        session.rollback()
        return []
    finally:
        session.close()

async def test_reminders():
    """Тестирует отправку напоминаний"""
    print("🚀 ТЕСТ НАПОМИНАНИЙ О БЮДЖЕТЕ")
    print("="*50)
    
    # Создаем турниры
    tournaments = await create_tournaments_for_reminders()
    
    if not tournaments:
        print("❌ Не удалось создать тестовые турниры")
        return
    
    # Создаем сервис с тестовым ботом
    test_bot = TestBot()
    budget_service = BudgetService(test_bot)
    
    print(f"\n🧪 Отправка напоминаний для {len(tournaments)} турниров...")
    
    # Отправляем напоминания
    reminders_sent = await budget_service.send_budget_reminders()
    
    print(f"\n📊 Результат: отправлено {reminders_sent} напоминаний")
    
    if reminders_sent > 0:
        print("✅ Напоминания работают корректно!")
    else:
        print("⚠️ Напоминания не отправлены. Проверьте логику времени.")
    
    # Тестируем установку бюджета для одного турнира
    print(f"\n🧪 Тестирование установки бюджета...")
    
    session = SessionLocal()
    try:
        tournament = session.query(Tournament).filter(
            Tournament.name == "Тест напоминаний - Одиночный турнир"
        ).first()
        
        if tournament:
            # Устанавливаем бюджет
            success = await budget_service.set_tournament_budget(tournament.tournament_id, 8000.0)
            
            if success:
                print("✅ Бюджет 8,000 руб. установлен успешно")
                
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
        
    except Exception as e:
        print(f"❌ Ошибка при установке бюджета: {e}")
    finally:
        session.close()
    
    # Очищаем тестовые данные
    print(f"\n🧹 Очистка тестовых данных...")
    
    session = SessionLocal()
    try:
        session.query(TournamentBudget).filter(
            TournamentBudget.tournament_id.in_(
                session.query(Tournament.tournament_id).filter(
                    Tournament.name.like("Тест напоминаний%")
                )
            )
        ).delete()
        session.query(Tournament).filter(Tournament.name.like("Тест напоминаний%")).delete()
        session.commit()
        print("✅ Тестовые данные очищены")
        
    except Exception as e:
        print(f"❌ Ошибка при очистке: {e}")
    finally:
        session.close()
    
    print(f"\n🎉 Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(test_reminders())
