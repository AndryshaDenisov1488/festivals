#!/usr/bin/env python3
"""
Скрипт для восстановления поврежденной базы данных SQLite.
Использует встроенные инструменты SQLite для проверки и восстановления.
"""

import os
import sys
import sqlite3
import shutil
from datetime import datetime
from config import DATABASE_URL

def get_db_path():
    """Получает путь к файлу базы данных"""
    if DATABASE_URL.startswith("sqlite:///"):
        db_path = DATABASE_URL.replace("sqlite:///", "")
        if not os.path.isabs(db_path):
            # Относительный путь - относительно текущей директории
            db_path = os.path.join(os.getcwd(), db_path)
        return db_path
    else:
        print(f"❌ Не SQLite база данных: {DATABASE_URL}")
        sys.exit(1)

def check_integrity(db_path):
    """Проверяет целостность базы данных"""
    print(f"🔍 Проверка целостности базы данных: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверка целостности
        cursor.execute("PRAGMA integrity_check;")
        result = cursor.fetchone()
        
        conn.close()
        
        if result[0] == "ok":
            print("✅ База данных целостна!")
            return True
        else:
            print(f"❌ База данных повреждена: {result[0]}")
            return False
            
    except sqlite3.DatabaseError as e:
        print(f"❌ Ошибка при проверке: {e}")
        return False

def create_backup(db_path):
    """Создает резервную копию базы данных"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"
    
    print(f"💾 Создание резервной копии: {backup_path}")
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"✅ Резервная копия создана: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Ошибка при создании резервной копии: {e}")
        return None

def repair_database(db_path):
    """Восстанавливает базу данных"""
    print(f"🔧 Восстановление базы данных: {db_path}")
    
    # Создаем резервную копию
    backup_path = create_backup(db_path)
    if not backup_path:
        print("❌ Не удалось создать резервную копию. Прерываем операцию.")
        return False
    
    # Создаем временный файл для восстановленной базы
    repaired_path = f"{db_path}.repaired"
    
    try:
        # Метод 1: Используем .dump и .read
        print("📤 Экспорт данных из поврежденной базы...")
        
        # Пытаемся экспортировать данные
        conn_old = sqlite3.connect(db_path)
        conn_new = sqlite3.connect(repaired_path)
        
        # Копируем схему и данные
        try:
            # Экспортируем данные через dump
            for line in conn_old.iterdump():
                try:
                    conn_new.executescript(line)
                except sqlite3.Error as e:
                    print(f"⚠️  Пропущена строка из-за ошибки: {e}")
                    continue
            
            conn_new.commit()
            conn_new.close()
            conn_old.close()
            
            print("✅ Данные экспортированы")
            
        except Exception as e:
            print(f"⚠️  Ошибка при экспорте: {e}")
            conn_old.close()
            conn_new.close()
            os.remove(repaired_path)
            
            # Метод 2: Используем .recover (требует sqlite3 3.38+)
            print("🔄 Попытка восстановления через .recover...")
            try:
                import subprocess
                
                # Используем sqlite3 CLI для восстановления
                result = subprocess.run(
                    ['sqlite3', db_path, '.recover'],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    # Сохраняем восстановленные данные
                    with open(repaired_path, 'w', encoding='utf-8') as f:
                        f.write(result.stdout)
                    
                    # Создаем новую базу из восстановленных данных
                    conn_new = sqlite3.connect(repaired_path)
                    conn_new.close()
                    
                    print("✅ Восстановление через .recover успешно")
                else:
                    print(f"❌ Ошибка при восстановлении через .recover: {result.stderr}")
                    return False
                    
            except FileNotFoundError:
                print("⚠️  sqlite3 CLI не найден. Пропускаем метод .recover")
                return False
            except Exception as e:
                print(f"❌ Ошибка при восстановлении: {e}")
                return False
        
        # Проверяем восстановленную базу
        if check_integrity(repaired_path):
            # Заменяем старую базу на восстановленную
            print("🔄 Замена базы данных...")
            os.replace(repaired_path, db_path)
            print("✅ База данных восстановлена и заменена!")
            return True
        else:
            print("❌ Восстановленная база данных все еще повреждена")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при восстановлении: {e}")
        if os.path.exists(repaired_path):
            os.remove(repaired_path)
        return False

def main():
    """Основная функция"""
    print("=" * 80)
    print("🔧 ВОССТАНОВЛЕНИЕ БАЗЫ ДАННЫХ SQLite")
    print("=" * 80)
    print()
    
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        print(f"❌ Файл базы данных не найден: {db_path}")
        sys.exit(1)
    
    print(f"📁 Путь к базе данных: {db_path}")
    print()
    
    # Проверяем целостность
    if check_integrity(db_path):
        print("✅ База данных не требует восстановления.")
        return
    
    print()
    print("⚠️  База данных повреждена. Начинаем восстановление...")
    print()
    
    # Восстанавливаем
    if repair_database(db_path):
        print()
        print("=" * 80)
        print("✅ ВОССТАНОВЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО")
        print("=" * 80)
        print()
        print("💡 Рекомендуется:")
        print("   1. Проверить работу бота")
        print("   2. Создать полную резервную копию базы данных")
        print("   3. Проверить логи на наличие других ошибок")
    else:
        print()
        print("=" * 80)
        print("❌ ВОССТАНОВЛЕНИЕ НЕ УДАЛОСЬ")
        print("=" * 80)
        print()
        print("💡 Рекомендуется:")
        print("   1. Использовать резервную копию базы данных")
        print("   2. Обратиться к администратору базы данных")
        print("   3. Проверить диск на наличие ошибок")
        sys.exit(1)

if __name__ == "__main__":
    main()

