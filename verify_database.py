#!/usr/bin/env python3
"""
Проверка целостности данных в БД.
Подсчёт турниров по месяцам, проверка на пустые month, дубликаты.
"""
import sys
from collections import defaultdict

from config import DATABASE_URL
from database import SessionLocal
from models import Tournament, Registration, User, JudgePayment


def get_db_path():
    if not DATABASE_URL.startswith("sqlite:///"):
        return None
    path = DATABASE_URL.replace("sqlite:///", "").replace("sqlite://", "")
    if not path.startswith("/") and ":" not in path[:2]:
        import os
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
    return path


def verify_tournaments(session):
    """Проверка турниров: подсчёт по месяцам, пустые month, дубликаты."""
    print("\n📊 ТУРНИРЫ")
    print("=" * 50)

    total = session.query(Tournament).count()
    print(f"Всего турниров: {total}")

    # По месяцам
    by_month = defaultdict(list)
    empty_month = []
    for t in session.query(Tournament).order_by(Tournament.date).all():
        if not t.month or not t.month.strip():
            empty_month.append((t.tournament_id, t.date, t.name))
        else:
            by_month[t.month].append(t)

    if empty_month:
        print(f"\n⚠️  Турниры с пустым month ({len(empty_month)}):")
        for tid, d, n in empty_month[:10]:
            print(f"   ID {tid}: {d} — {n}")
        if len(empty_month) > 10:
            print(f"   ... и ещё {len(empty_month) - 10}")

    MONTH_ORDER = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                   "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]

    def month_sort_key(m):
        for i, name in enumerate(MONTH_ORDER):
            if m.lower() == name.lower():
                return i
        return 99

    print("\n📅 Турниры по месяцам:")
    for month in sorted(by_month.keys(), key=month_sort_key):
        count = len(by_month[month])
        dates = sorted(set(t.date for t in by_month[month]))
        date_range = f"{dates[0]} — {dates[-1]}" if dates else "—"
        print(f"   {month}: {count} турниров (даты: {date_range})")

    # Варианты написания месяцев (если есть "февраль" и "Февраль")
    month_variants = defaultdict(int)
    for t in session.query(Tournament).all():
        if t.month:
            month_variants[t.month] += 1
    if len(month_variants) > 12:
        print("\n⚠️  Разные варианты написания месяцев (могут быть дубли кнопок):")
        for m, c in sorted(month_variants.items(), key=lambda x: -x[1]):
            print(f"   '{m}': {c}")

    return total, len(empty_month)


def verify_registrations(session):
    """Проверка заявок."""
    print("\n📋 ЗАЯВКИ")
    print("=" * 50)
    try:
        total = session.query(Registration).count()
        valid_tournament_ids = {t[0] for t in session.query(Tournament.tournament_id).all()}
        orphaned = sum(
            1 for r in session.query(Registration).all()
            if r.tournament_id not in valid_tournament_ids
        )
        print(f"Всего заявок: {total}")
        if orphaned:
            print(f"⚠️  Заявок без турнира (битые ссылки): {orphaned}")
    except Exception as e:
        print(f"❌ Ошибка при проверке заявок: {e}")
        print("   ⚠️  БД повреждена! Восстановите из бэкапа:")
        print("   1. Остановите бота: sudo systemctl stop judges-bot judges-api")
        print("   2. python restore_database.py /path/to/good/bot_database.db")
        print("   3. sudo systemctl start judges-bot judges-api")
    return 0


def verify_payments(session):
    """Проверка записей об оплате."""
    print("\n💰 ОПЛАТЫ")
    print("=" * 50)
    try:
        total = session.query(JudgePayment).count()
        valid_tournament_ids = {t[0] for t in session.query(Tournament.tournament_id).all()}
        orphaned = sum(
            1 for p in session.query(JudgePayment).all()
            if p.tournament_id not in valid_tournament_ids
        )
        print(f"Всего записей об оплате: {total}")
        if orphaned:
            print(f"⚠️  Оплат без турнира (битые ссылки): {orphaned}")
    except Exception as e:
        print(f"❌ Ошибка при проверке оплат: {e}")
    return 0


def main():
    db_path = get_db_path()
    if db_path:
        import os
        if not os.path.exists(db_path):
            print(f"❌ Файл БД не найден: {db_path}")
            sys.exit(1)
        print(f"📁 БД: {db_path}")
        print(f"   Размер: {os.path.getsize(db_path) / 1024:.1f} KB")

    session = SessionLocal()
    try:
        verify_tournaments(session)
        verify_registrations(session)
        verify_payments(session)
        print("\n✅ Проверка завершена.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
