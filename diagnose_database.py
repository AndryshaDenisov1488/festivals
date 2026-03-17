#!/usr/bin/env python3
"""
Скрипт для диагностики проблем с базой данных SQLite.
Проверяет целостность, WAL файлы, размер базы и другие параметры.
"""

import os
import sys
import sqlite3
from config import DATABASE_URL

def get_db_path():
    """Получает путь к файлу базы данных"""
    if DATABASE_URL.startswith("sqlite:///"):
        db_path = DATABASE_URL.replace("sqlite:///", "")
        if not os.path.isabs(db_path):
            db_path = os.path.join(os.getcwd(), db_path)
        return db_path
    else:
        print(f"❌ Не SQLite база данных: {DATABASE_URL}")
        sys.exit(1)

def check_database_health(db_path):
    """Проверяет здоровье базы данных"""
    print("=" * 80)
    print("🔍 ДИАГНОСТИКА БАЗЫ ДАННЫХ")
    print("=" * 80)
    print()
    
    # Проверка существования файла
    if not os.path.exists(db_path):
        print(f"❌ Файл базы данных не найден: {db_path}")
        return False
    
    print(f"📁 Путь к базе данных: {db_path}")
    print()
    
    # Размер файла
    db_size = os.path.getsize(db_path)
    print(f"📊 Размер базы данных: {db_size / 1024 / 1024:.2f} MB")
    print()
    
    # Проверка WAL файлов
    wal_path = f"{db_path}-wal"
    shm_path = f"{db_path}-shm"
    
    print("🔍 Проверка WAL файлов:")
    if os.path.exists(wal_path):
        wal_size = os.path.getsize(wal_path)
        print(f"   ⚠️  WAL файл найден: {wal_path} ({wal_size / 1024:.2f} KB)")
        print("   💡 WAL файл может быть причиной проблем!")
    else:
        print(f"   ✅ WAL файл не найден (это нормально)")
    
    if os.path.exists(shm_path):
        shm_size = os.path.getsize(shm_path)
        print(f"   ⚠️  SHM файл найден: {shm_path} ({shm_size} bytes)")
    else:
        print(f"   ✅ SHM файл не найден (это нормально)")
    print()
    
    # Попытка подключения
    print("🔌 Попытка подключения к базе данных...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверка режима журнала
        cursor.execute("PRAGMA journal_mode;")
        journal_mode = cursor.fetchone()[0]
        print(f"   📝 Режим журнала: {journal_mode}")
        
        # Проверка целостности
        print()
        print("🔍 Проверка целостности базы данных...")
        cursor.execute("PRAGMA integrity_check;")
        integrity_result = cursor.fetchone()[0]
        
        if integrity_result == "ok":
            print("   ✅ База данных целостна!")
        else:
            print(f"   ❌ База данных повреждена: {integrity_result[:200]}")
            if len(integrity_result) > 200:
                print(f"   ... (сообщение обрезано)")
        
        # Проверка быстрой целостности
        print()
        print("🔍 Быстрая проверка целостности...")
        cursor.execute("PRAGMA quick_check;")
        quick_check = cursor.fetchone()[0]
        
        if quick_check == "ok":
            print("   ✅ Быстрая проверка пройдена!")
        else:
            print(f"   ❌ Быстрая проверка не пройдена: {quick_check[:200]}")
        
        # Статистика таблиц
        print()
        print("📊 Статистика таблиц:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table_name, in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = cursor.fetchone()[0]
                print(f"   📋 {table_name}: {count} записей")
            except sqlite3.Error as e:
                print(f"   ❌ {table_name}: ошибка при чтении - {e}")
        
        conn.close()
        print()
        print("=" * 80)
        
        if integrity_result == "ok" and quick_check == "ok":
            print("✅ БАЗА ДАННЫХ В НОРМАЛЬНОМ СОСТОЯНИИ")
            return True
        else:
            print("❌ БАЗА ДАННЫХ ПОВРЕЖДЕНА")
            return False
            
    except sqlite3.DatabaseError as e:
        error_msg = str(e)
        print(f"   ❌ Ошибка подключения: {error_msg}")
        
        if "malformed" in error_msg.lower():
            print()
            print("=" * 80)
            print("❌ БАЗА ДАННЫХ ПОВРЕЖДЕНА (database disk image is malformed)")
            print("=" * 80)
            print()
            print("💡 ВОЗМОЖНЫЕ ПРИЧИНЫ:")
            print("   1. WAL файлы повреждены или не синхронизированы")
            print("   2. Неожиданное завершение работы во время записи")
            print("   3. Проблемы с диском (нехватка места, ошибки диска)")
            print("   4. Одновременный доступ к базе данных")
            print()
            print("🔧 РЕКОМЕНДАЦИИ:")
            print("   1. Удалите WAL файлы (если они есть):")
            print(f"      rm -f {wal_path} {shm_path}")
            print("   2. Попробуйте восстановить через repair_database.py")
            print("   3. Используйте резервную копию базы данных")
            print("   4. Проверьте место на диске: df -h")
            print("   5. Проверьте логи системы: dmesg | grep -i error")
        
        return False
    except Exception as e:
        print(f"   ❌ Неожиданная ошибка: {e}")
        return False

def fix_wal_files(db_path):
    """Пытается исправить проблемы с WAL файлами"""
    wal_path = f"{db_path}-wal"
    shm_path = f"{db_path}-shm"
    
    print()
    print("🔧 Попытка исправления WAL файлов...")
    
    if os.path.exists(wal_path) or os.path.exists(shm_path):
        print("   ⚠️  Найдены WAL файлы. Попытка закрыть WAL режим...")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Пытаемся переключиться в DELETE режим (закроет WAL)
            cursor.execute("PRAGMA journal_mode=DELETE;")
            result = cursor.fetchone()[0]
            print(f"   📝 Режим журнала изменен на: {result}")
            
            conn.close()
            
            # Удаляем WAL файлы
            if os.path.exists(wal_path):
                os.remove(wal_path)
                print(f"   ✅ Удален WAL файл: {wal_path}")
            
            if os.path.exists(shm_path):
                os.remove(shm_path)
                print(f"   ✅ Удален SHM файл: {shm_path}")
            
            print("   ✅ WAL файлы обработаны")
            return True
            
        except Exception as e:
            print(f"   ❌ Ошибка при обработке WAL файлов: {e}")
            return False
    else:
        print("   ✅ WAL файлы не найдены")
        return True

def main():
    """Основная функция"""
    db_path = get_db_path()
    
    # Диагностика
    is_healthy = check_database_health(db_path)
    
    if not is_healthy:
        print()
        response = input("Попытаться исправить WAL файлы? (yes/no): ")
        if response.lower() in ['yes', 'y', 'да', 'д']:
            fix_wal_files(db_path)
            print()
            print("🔄 Повторная проверка после исправления...")
            check_database_health(db_path)

if __name__ == "__main__":
    main()

