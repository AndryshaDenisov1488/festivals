#!/usr/bin/env python3
"""
Комплексная проверка базы данных.
Проверяет целостность, структуру, данные и выявляет проблемы.
"""

import os
import sys
import sqlite3
from datetime import datetime
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import User, Tournament, Registration, JudgePayment, RegistrationStatus
from sqlalchemy import func, and_
from sqlalchemy.exc import SQLAlchemyError

# Константы
STANDARD_PAYMENT_AMOUNT = 5000
SPECIAL_JUDGE_ID = 946719504  # Лизочка Маркова
MIN_PAYMENT_AMOUNT = 3500

def check_database_integrity(db_path):
    """Проверяет целостность базы данных SQLite"""
    print("=" * 80)
    print("🔍 ПРОВЕРКА ЦЕЛОСТНОСТИ БАЗЫ ДАННЫХ")
    print("=" * 80)
    print()
    
    issues = []
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверка целостности
        print("📋 Проверка целостности...")
        cursor.execute("PRAGMA integrity_check;")
        integrity_result = cursor.fetchone()[0]
        
        if integrity_result == "ok":
            print("   ✅ База данных целостна")
        else:
            print(f"   ❌ База данных повреждена: {integrity_result[:200]}")
            issues.append("База данных повреждена")
        
        # Быстрая проверка
        print("📋 Быстрая проверка...")
        cursor.execute("PRAGMA quick_check;")
        quick_check = cursor.fetchone()[0]
        
        if quick_check == "ok":
            print("   ✅ Быстрая проверка пройдена")
        else:
            print(f"   ❌ Быстрая проверка не пройдена: {quick_check[:200]}")
            issues.append("Быстрая проверка не пройдена")
        
        # Проверка внешних ключей
        print("📋 Проверка внешних ключей...")
        cursor.execute("PRAGMA foreign_key_check;")
        fk_issues = cursor.fetchall()
        
        if not fk_issues:
            print("   ✅ Внешние ключи в порядке")
        else:
            print(f"   ⚠️  Найдено проблем с внешними ключами: {len(fk_issues)}")
            issues.append(f"Проблемы с внешними ключами: {len(fk_issues)}")
        
        conn.close()
        
    except sqlite3.DatabaseError as e:
        print(f"   ❌ Ошибка при проверке: {e}")
        issues.append(f"Ошибка базы данных: {e}")
    except Exception as e:
        print(f"   ❌ Неожиданная ошибка: {e}")
        issues.append(f"Неожиданная ошибка: {e}")
    
    print()
    return issues

def check_database_structure():
    """Проверяет структуру базы данных"""
    print("=" * 80)
    print("📊 ПРОВЕРКА СТРУКТУРЫ БАЗЫ ДАННЫХ")
    print("=" * 80)
    print()
    
    session = SessionLocal()
    issues = []
    
    try:
        # Проверка таблиц
        print("📋 Проверка таблиц...")
        
        tables = ['users', 'tournaments', 'registrations', 'judge_payments', 'tournament_budgets']
        
        for table in tables:
            try:
                from sqlalchemy import text
                result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"   ✅ {table}: {count} записей")
            except Exception as e:
                print(f"   ❌ {table}: ошибка - {e}")
                issues.append(f"Проблема с таблицей {table}: {e}")
        
        print()
        
    except Exception as e:
        print(f"❌ Ошибка при проверке структуры: {e}")
        issues.append(f"Ошибка проверки структуры: {e}")
    finally:
        session.close()
    
    return issues

def check_users_data():
    """Проверяет данные пользователей"""
    print("=" * 80)
    print("👥 ПРОВЕРКА ДАННЫХ ПОЛЬЗОВАТЕЛЕЙ")
    print("=" * 80)
    print()
    
    session = SessionLocal()
    issues = []
    
    try:
        users = session.query(User).all()
        print(f"📊 Всего пользователей: {len(users)}")
        
        # Проверка на пустые имена
        empty_names = [u for u in users if not u.first_name or not u.last_name]
        if empty_names:
            print(f"   ⚠️  Пользователей с пустыми именами: {len(empty_names)}")
            issues.append(f"Пользователи с пустыми именами: {len(empty_names)}")
        
        # Проверка дубликатов
        user_ids = [u.user_id for u in users]
        duplicates = [uid for uid in user_ids if user_ids.count(uid) > 1]
        if duplicates:
            print(f"   ⚠️  Дубликаты user_id: {len(set(duplicates))}")
            issues.append(f"Дубликаты user_id: {len(set(duplicates))}")
        
        print(f"   ✅ Всего пользователей: {len(users)}")
        print()
        
    except Exception as e:
        print(f"❌ Ошибка при проверке пользователей: {e}")
        issues.append(f"Ошибка проверки пользователей: {e}")
    finally:
        session.close()
    
    return issues

def check_tournaments_data():
    """Проверяет данные турниров"""
    print("=" * 80)
    print("🏆 ПРОВЕРКА ДАННЫХ ТУРНИРОВ")
    print("=" * 80)
    print()
    
    session = SessionLocal()
    issues = []
    
    try:
        tournaments = session.query(Tournament).all()
        print(f"📊 Всего турниров: {len(tournaments)}")
        
        # Проверка на пустые названия
        empty_names = [t for t in tournaments if not t.name]
        if empty_names:
            print(f"   ⚠️  Турниров с пустыми названиями: {len(empty_names)}")
            issues.append(f"Турниры с пустыми названиями: {len(empty_names)}")
        
        # Проверка дубликатов
        tournament_ids = [t.tournament_id for t in tournaments]
        duplicates = [tid for tid in tournament_ids if tournament_ids.count(tid) > 1]
        if duplicates:
            print(f"   ⚠️  Дубликаты tournament_id: {len(set(duplicates))}")
            issues.append(f"Дубликаты tournament_id: {len(set(duplicates))}")
        
        print(f"   ✅ Всего турниров: {len(tournaments)}")
        print()
        
    except Exception as e:
        print(f"❌ Ошибка при проверке турниров: {e}")
        issues.append(f"Ошибка проверки турниров: {e}")
    finally:
        session.close()
    
    return issues

def check_registrations_data():
    """Проверяет данные регистраций"""
    print("=" * 80)
    print("📝 ПРОВЕРКА ДАННЫХ РЕГИСТРАЦИЙ")
    print("=" * 80)
    print()
    
    session = SessionLocal()
    issues = []
    
    try:
        registrations = session.query(Registration).all()
        print(f"📊 Всего регистраций: {len(registrations)}")
        
        # Проверка на несуществующих пользователей
        user_ids = {u.user_id for u in session.query(User.user_id).all()}
        invalid_users = [r for r in registrations if r.user_id not in user_ids]
        if invalid_users:
            print(f"   ⚠️  Регистраций с несуществующими пользователями: {len(invalid_users)}")
            issues.append(f"Регистрации с несуществующими пользователями: {len(invalid_users)}")
        
        # Проверка на несуществующие турниры
        tournament_ids = {t.tournament_id for t in session.query(Tournament.tournament_id).all()}
        invalid_tournaments = [r for r in registrations if r.tournament_id not in tournament_ids]
        if invalid_tournaments:
            print(f"   ⚠️  Регистраций с несуществующими турнирами: {len(invalid_tournaments)}")
            issues.append(f"Регистрации с несуществующими турнирами: {len(invalid_tournaments)}")
        
        # Статистика по статусам
        status_counts = defaultdict(int)
        for reg in registrations:
            status_counts[reg.status] += 1
        
        print("   📊 Статистика по статусам:")
        for status, count in status_counts.items():
            print(f"      {status}: {count}")
        
        print(f"   ✅ Всего регистраций: {len(registrations)}")
        print()
        
    except Exception as e:
        print(f"❌ Ошибка при проверке регистраций: {e}")
        issues.append(f"Ошибка проверки регистраций: {e}")
    finally:
        session.close()
    
    return issues

def check_payments_data():
    """Проверяет данные об оплатах"""
    print("=" * 80)
    print("💰 ПРОВЕРКА ДАННЫХ ОБ ОПЛАТАХ")
    print("=" * 80)
    print()
    
    session = SessionLocal()
    issues = []
    
    try:
        payments = session.query(JudgePayment).all()
        print(f"📊 Всего записей об оплате: {len(payments)}")
        print()
        
        # 1. Неоплаченные записи
        unpaid = [p for p in payments if not p.is_paid]
        print(f"1️⃣  НЕОПЛАЧЕННЫЕ ЗАПИСИ: {len(unpaid)}")
        if unpaid:
            issues.append(f"Неоплаченные записи: {len(unpaid)}")
        
        # 2. Оплаченные записи
        paid = [p for p in payments if p.is_paid]
        print(f"2️⃣  ОПЛАЧЕННЫЕ ЗАПИСИ: {len(paid)}")
        
        # 3. Записи с некорректными суммами
        print()
        print("3️⃣  ПРОВЕРКА СУММ ОПЛАТЫ:")
        
        incorrect_amounts = []
        missing_amounts = []
        
        for payment in paid:
            if payment.amount is None:
                missing_amounts.append(payment)
            elif payment.user_id == SPECIAL_JUDGE_ID:
                # Для Лизочки Марковой - любая сумма допустима
                pass
            elif payment.amount < MIN_PAYMENT_AMOUNT:
                incorrect_amounts.append(payment)
            elif payment.amount != STANDARD_PAYMENT_AMOUNT:
                incorrect_amounts.append(payment)
        
        if missing_amounts:
            print(f"   ⚠️  Записей без суммы: {len(missing_amounts)}")
            issues.append(f"Записи без суммы: {len(missing_amounts)}")
            for p in missing_amounts[:5]:  # Показываем первые 5
                user = session.query(User).filter(User.user_id == p.user_id).first()
                tournament = session.query(Tournament).filter(Tournament.tournament_id == p.tournament_id).first()
                if user and tournament:
                    print(f"      - {user.first_name} {user.last_name} ({p.user_id}) - {tournament.name} ({tournament.date.strftime('%d.%m.%Y')})")
        
        if incorrect_amounts:
            print(f"   ⚠️  Записей с некорректной суммой: {len(incorrect_amounts)}")
            issues.append(f"Записи с некорректной суммой: {len(incorrect_amounts)}")
            for p in incorrect_amounts[:5]:  # Показываем первые 5
                user = session.query(User).filter(User.user_id == p.user_id).first()
                tournament = session.query(Tournament).filter(Tournament.tournament_id == p.tournament_id).first()
                if user and tournament:
                    print(f"      - {user.first_name} {user.last_name} ({p.user_id}) - {tournament.name} ({tournament.date.strftime('%d.%m.%Y')}) - {p.amount} руб.")
        
        # 4. Записи для неутвержденных судей
        print()
        print("4️⃣  ПРОВЕРКА СООТВЕТСТВИЯ СТАТУСУ РЕГИСТРАЦИИ:")
        
        invalid_status_payments = []
        for payment in payments:
            registration = session.query(Registration).filter(
                and_(
                    Registration.user_id == payment.user_id,
                    Registration.tournament_id == payment.tournament_id
                )
            ).first()
            
            if not registration:
                invalid_status_payments.append((payment, "регистрация удалена"))
            elif registration.status != RegistrationStatus.APPROVED:
                invalid_status_payments.append((payment, f"статус: {registration.status}"))
        
        if invalid_status_payments:
            print(f"   ⚠️  Записей об оплате для неутвержденных/удаленных регистраций: {len(invalid_status_payments)}")
            issues.append(f"Записи для неутвержденных регистраций: {len(invalid_status_payments)}")
            for payment, reason in invalid_status_payments[:5]:  # Показываем первые 5
                user = session.query(User).filter(User.user_id == payment.user_id).first()
                tournament = session.query(Tournament).filter(Tournament.tournament_id == payment.tournament_id).first()
                if user and tournament:
                    print(f"      - {user.first_name} {user.last_name} ({payment.user_id}) - {tournament.name} ({tournament.date.strftime('%d.%m.%Y')}) - {reason}")
        
        # 5. Статистика по суммам
        print()
        print("5️⃣  СТАТИСТИКА ПО СУММАМ:")
        
        if paid:
            amounts = [p.amount for p in paid if p.amount is not None]
            if amounts:
                print(f"   Минимальная сумма: {min(amounts)} руб.")
                print(f"   Максимальная сумма: {max(amounts)} руб.")
                print(f"   Средняя сумма: {sum(amounts) / len(amounts):.2f} руб.")
                print(f"   Общая сумма: {sum(amounts):.2f} руб.")
        
        print()
        print(f"   ✅ Всего записей об оплате: {len(payments)}")
        print()
        
    except Exception as e:
        print(f"❌ Ошибка при проверке оплат: {e}")
        import traceback
        traceback.print_exc()
        issues.append(f"Ошибка проверки оплат: {e}")
    finally:
        session.close()
    
    return issues

def generate_report(all_issues):
    """Генерирует итоговый отчет"""
    print("=" * 80)
    print("📋 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 80)
    print()
    
    if not all_issues:
        print("✅ Все проверки пройдены успешно!")
        print("   База данных в хорошем состоянии.")
    else:
        print(f"⚠️  Найдено проблем: {len(all_issues)}")
        print()
        print("Список проблем:")
        for i, issue in enumerate(all_issues, 1):
            print(f"   {i}. {issue}")
    
    print()
    print("=" * 80)
    
    # Сохраняем отчет в файл
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"database_check_report_{timestamp}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("ОТЧЕТ О ПРОВЕРКЕ БАЗЫ ДАННЫХ\n")
        f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        if not all_issues:
            f.write("✅ Все проверки пройдены успешно!\n")
        else:
            f.write(f"⚠️  Найдено проблем: {len(all_issues)}\n\n")
            f.write("Список проблем:\n")
            for i, issue in enumerate(all_issues, 1):
                f.write(f"   {i}. {issue}\n")
    
    print(f"📄 Отчет сохранен в файл: {report_file}")
    print()

def main():
    """Основная функция"""
    print("=" * 80)
    print("🔍 КОМПЛЕКСНАЯ ПРОВЕРКА БАЗЫ ДАННЫХ")
    print("=" * 80)
    print()
    
    from config import DATABASE_URL
    
    # Получаем путь к базе данных
    if DATABASE_URL.startswith("sqlite:///"):
        db_path = DATABASE_URL.replace("sqlite:///", "")
        if not os.path.isabs(db_path):
            db_path = os.path.join(os.getcwd(), db_path)
    else:
        print(f"❌ Не SQLite база данных: {DATABASE_URL}")
        sys.exit(1)
    
    if not os.path.exists(db_path):
        print(f"❌ Файл базы данных не найден: {db_path}")
        sys.exit(1)
    
    print(f"📁 Путь к базе данных: {db_path}")
    print()
    
    all_issues = []
    
    # 1. Проверка целостности
    integrity_issues = check_database_integrity(db_path)
    all_issues.extend(integrity_issues)
    
    # 2. Проверка структуры
    structure_issues = check_database_structure()
    all_issues.extend(structure_issues)
    
    # 3. Проверка данных пользователей
    users_issues = check_users_data()
    all_issues.extend(users_issues)
    
    # 4. Проверка данных турниров
    tournaments_issues = check_tournaments_data()
    all_issues.extend(tournaments_issues)
    
    # 5. Проверка данных регистраций
    registrations_issues = check_registrations_data()
    all_issues.extend(registrations_issues)
    
    # 6. Проверка данных об оплатах
    payments_issues = check_payments_data()
    all_issues.extend(payments_issues)
    
    # Итоговый отчет
    generate_report(all_issues)
    
    if all_issues:
        print("💡 Рекомендации:")
        print("   1. Исправьте найденные проблемы")
        print("   2. Используйте скрипты fix_payment_issues.py для исправления оплат")
        print("   3. Используйте mass_update_payments.py для массового обновления")
        return 1
    else:
        return 0

if __name__ == "__main__":
    sys.exit(main())

