# cleanup_test_data.py
"""
Скрипт для очистки тестовых данных из базы данных
"""

import logging
from database import SessionLocal
from models import User, Tournament, Registration, JudgePayment

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_test_data():
    """Удаляет тестовые данные из базы данных"""
    session = SessionLocal()
    
    try:
        print("🧹 Начинаем очистку тестовых данных...")
        
        # 1. Удаляем тестовых пользователей (ID 2000+)
        test_users = session.query(User).filter(User.user_id >= 2000).all()
        if test_users:
            print(f"📝 Найдено {len(test_users)} тестовых пользователей")
            for user in test_users:
                print(f"   - {user.first_name} {user.last_name} (ID: {user.user_id})")
            
            # Удаляем связанные записи
            for user in test_users:
                # Удаляем записи об оплате
                session.query(JudgePayment).filter(JudgePayment.user_id == user.user_id).delete()
                # Удаляем регистрации
                session.query(Registration).filter(Registration.user_id == user.user_id).delete()
            
            # Удаляем пользователей
            session.query(User).filter(User.user_id >= 2000).delete()
            print("✅ Тестовые пользователи удалены")
        else:
            print("ℹ️ Тестовых пользователей не найдено")
        
        # 2. Удаляем тестовые турниры
        test_tournaments = session.query(Tournament).filter(
            Tournament.name.like('%Тест%')
        ).all()
        if test_tournaments:
            print(f"🏆 Найдено {len(test_tournaments)} тестовых турниров")
            for tournament in test_tournaments:
                print(f"   - {tournament.name} ({tournament.date})")
            
            # Удаляем связанные записи
            for tournament in test_tournaments:
                # Удаляем записи об оплате
                session.query(JudgePayment).filter(JudgePayment.tournament_id == tournament.tournament_id).delete()
                # Удаляем регистрации
                session.query(Registration).filter(Registration.tournament_id == tournament.tournament_id).delete()
            
            # Удаляем турниры
            session.query(Tournament).filter(Tournament.name.like('%Тест%')).delete()
            print("✅ Тестовые турниры удалены")
        else:
            print("ℹ️ Тестовых турниров не найдено")
        
        # 3. Удаляем тестовые записи об оплате (если остались)
        test_payments = session.query(JudgePayment).join(User).filter(
            User.user_id >= 2000
        ).all()
        if test_payments:
            print(f"💰 Найдено {len(test_payments)} тестовых записей об оплате")
            session.query(JudgePayment).join(User).filter(User.user_id >= 2000).delete()
            print("✅ Тестовые записи об оплате удалены")
        else:
            print("ℹ️ Тестовых записей об оплате не найдено")
        
        # 4. Удаляем тестовые регистрации (если остались)
        test_registrations = session.query(Registration).join(User).filter(
            User.user_id >= 2000
        ).all()
        if test_registrations:
            print(f"📝 Найдено {len(test_registrations)} тестовых регистраций")
            session.query(Registration).join(User).filter(User.user_id >= 2000).delete()
            print("✅ Тестовые регистрации удалены")
        else:
            print("ℹ️ Тестовых регистраций не найдено")
        
        session.commit()
        print("\n🎉 Очистка тестовых данных завершена успешно!")
        
        # Показываем статистику после очистки
        print("\n📊 Статистика после очистки:")
        print(f"   👥 Пользователей: {session.query(User).count()}")
        print(f"   🏆 Турниров: {session.query(Tournament).count()}")
        print(f"   📝 Регистраций: {session.query(Registration).count()}")
        print(f"   💰 Записей об оплате: {session.query(JudgePayment).count()}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при очистке тестовых данных: {e}")
        session.rollback()
        print(f"❌ Ошибка: {e}")
    finally:
        session.close()

def show_current_data():
    """Показывает текущие данные в базе"""
    session = SessionLocal()
    
    try:
        print("📊 ТЕКУЩИЕ ДАННЫЕ В БАЗЕ:")
        print("=" * 40)
        
        # Пользователи
        users = session.query(User).all()
        print(f"👥 Пользователей: {len(users)}")
        for user in users[:5]:  # Показываем первых 5
            print(f"   - {user.first_name} {user.last_name} (ID: {user.user_id})")
        if len(users) > 5:
            print(f"   ... и еще {len(users) - 5}")
        
        # Турниры
        tournaments = session.query(Tournament).all()
        print(f"\n🏆 Турниров: {len(tournaments)}")
        for tournament in tournaments[:5]:  # Показываем первых 5
            print(f"   - {tournament.name} ({tournament.date})")
        if len(tournaments) > 5:
            print(f"   ... и еще {len(tournaments) - 5}")
        
        # Регистрации
        registrations = session.query(Registration).count()
        print(f"\n📝 Регистраций: {registrations}")
        
        # Записи об оплате
        payments = session.query(JudgePayment).count()
        print(f"💰 Записей об оплате: {payments}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при получении данных: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    print("🔍 ПРОВЕРКА ТЕКУЩИХ ДАННЫХ")
    print("=" * 50)
    show_current_data()
    
    print("\n" + "=" * 50)
    response = input("\n❓ Удалить тестовые данные? (y/N): ").strip().lower()
    
    if response in ['y', 'yes', 'да', 'д']:
        cleanup_test_data()
    else:
        print("❌ Очистка отменена")
