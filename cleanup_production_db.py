#!/usr/bin/env python3
"""
Скрипт для очистки БД от тестовых данных перед продакшеном
Оставляет только судей, удаляет все остальное
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine
from models import Base, User, Tournament, Registration, JudgePayment, TournamentBudget
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_production_db():
    """Очистка БД от тестовых данных"""
    session = SessionLocal()
    try:
        logger.info("🧹 Начинаем очистку БД от тестовых данных...")
        
        # 1. Удаляем все турниры
        tournaments_count = session.query(Tournament).count()
        session.query(Tournament).delete()
        logger.info(f"❌ Удалено турниров: {tournaments_count}")
        
        # 2. Удаляем все записи на турниры
        registrations_count = session.query(Registration).count()
        session.query(Registration).delete()
        logger.info(f"❌ Удалено записей на турниры: {registrations_count}")
        
        # 3. Удаляем все платежи судей
        payments_count = session.query(JudgePayment).count()
        session.query(JudgePayment).delete()
        logger.info(f"❌ Удалено платежей судей: {payments_count}")
        
        # 4. Удаляем все бюджеты турниров
        budgets_count = session.query(TournamentBudget).count()
        session.query(TournamentBudget).delete()
        logger.info(f"❌ Удалено бюджетов турниров: {budgets_count}")
        
        # 5. Оставляем только судей
        users_count = session.query(User).count()
        logger.info(f"✅ Остается судей: {users_count}")
        
        # 6. Сбрасываем автоинкременты (если таблица существует)
        try:
            session.execute(text("DELETE FROM sqlite_sequence WHERE name IN ('tournaments', 'registrations', 'judge_payments', 'tournament_budgets')"))
        except Exception:
            # Таблица sqlite_sequence может не существовать - это нормально
            pass
        
        # 7. Коммитим изменения
        session.commit()
        
        logger.info("✅ Очистка БД завершена успешно!")
        logger.info("📊 Итоговая статистика:")
        logger.info(f"   👥 Судьи: {session.query(User).count()}")
        logger.info(f"   🏆 Турниры: {session.query(Tournament).count()}")
        logger.info(f"   📝 Записи: {session.query(Registration).count()}")
        logger.info(f"   💰 Платежи: {session.query(JudgePayment).count()}")
        logger.info(f"   💵 Бюджеты: {session.query(TournamentBudget).count()}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при очистке БД: {e}")
        session.rollback()
        raise
    finally:
        session.close()

def show_current_stats():
    """Показать текущую статистику БД"""
    session = SessionLocal()
    try:
        logger.info("📊 Текущая статистика БД:")
        logger.info(f"   👥 Судьи: {session.query(User).count()}")
        logger.info(f"   🏆 Турниры: {session.query(Tournament).count()}")
        logger.info(f"   📝 Записи: {session.query(Registration).count()}")
        logger.info(f"   💰 Платежи: {session.query(JudgePayment).count()}")
        logger.info(f"   💵 Бюджеты: {session.query(TournamentBudget).count()}")
        
        # Показать список судей
        users = session.query(User).all()
        if users:
            logger.info("👥 Список судей:")
            for user in users:
                logger.info(f"   - {user.first_name} {user.last_name} (ID: {user.user_id})")
        else:
            logger.info("👥 Судьи не найдены")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при получении статистики: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    print("🧹 ОЧИСТКА БД ОТ ТЕСТОВЫХ ДАННЫХ")
    print("=" * 50)
    
    # Показать текущую статистику
    show_current_stats()
    
    print("\n⚠️  ВНИМАНИЕ!")
    print("Этот скрипт удалит ВСЕ данные кроме судей:")
    print("- Все турниры")
    print("- Все записи на турниры") 
    print("- Все платежи судей")
    print("- Все бюджеты турниров")
    print("\nОстанутся только судьи!")
    
    confirm = input("\n❓ Продолжить? (yes/no): ").lower().strip()
    
    if confirm in ['yes', 'y', 'да', 'д']:
        cleanup_production_db()
        print("\n✅ Очистка завершена!")
    else:
        print("❌ Очистка отменена")

