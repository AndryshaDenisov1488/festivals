# restore_from_backup.py
"""
Скрипт для восстановления базы данных из резервной копии
"""

import os
import shutil
import glob
from datetime import datetime

def list_backups():
    """Показывает список доступных резервных копий"""
    backup_files = glob.glob("bot_database_season_*.db")
    backup_files.sort(reverse=True)  # Сортируем по дате (новые сверху)
    
    if not backup_files:
        print("❌ Резервные копии не найдены!")
        return []
    
    print("📁 ДОСТУПНЫЕ РЕЗЕРВНЫЕ КОПИИ:")
    print("=" * 50)
    
    for i, backup in enumerate(backup_files, 1):
        # Получаем информацию о файле
        stat = os.stat(backup)
        size_mb = stat.st_size / (1024 * 1024)
        mod_time = datetime.fromtimestamp(stat.st_mtime)
        
        print(f"{i}. {backup}")
        print(f"   📅 Создана: {mod_time.strftime('%d.%m.%Y %H:%M:%S')}")
        print(f"   📊 Размер: {size_mb:.2f} MB")
        print()
    
    return backup_files

def restore_backup(backup_file):
    """Восстанавливает базу из резервной копии"""
    current_db = "bot_database.db"
    
    if not os.path.exists(backup_file):
        print(f"❌ Файл резервной копии не найден: {backup_file}")
        return False
    
    try:
        # Создаем резервную копию текущей базы (если она существует)
        if os.path.exists(current_db):
            current_backup = f"bot_database_current_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(current_db, current_backup)
            print(f"✅ Текущая база сохранена как: {current_backup}")
        
        # Восстанавливаем из резервной копии
        shutil.copy2(backup_file, current_db)
        print(f"✅ База данных восстановлена из: {backup_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при восстановлении: {e}")
        return False

def main():
    """Основная функция восстановления"""
    print("🔄 ВОССТАНОВЛЕНИЕ БАЗЫ ДАННЫХ")
    print("=" * 40)
    
    # Показываем список резервных копий
    backups = list_backups()
    if not backups:
        return
    
    # Выбираем резервную копию
    try:
        choice = input(f"\nВыберите резервную копию (1-{len(backups)}): ").strip()
        index = int(choice) - 1
        
        if index < 0 or index >= len(backups):
            print("❌ Неверный выбор!")
            return
        
        selected_backup = backups[index]
        
    except ValueError:
        print("❌ Неверный ввод!")
        return
    
    # Подтверждение
    print(f"\n⚠️  ВНИМАНИЕ!")
    print(f"Вы собираетесь восстановить базу из: {selected_backup}")
    print("Текущая база будет заменена!")
    
    confirm = input("\nПродолжить? (да/нет): ").lower().strip()
    if confirm not in ['да', 'yes', 'y', 'д']:
        print("❌ Операция отменена")
        return
    
    # Восстанавливаем
    print(f"\n🔄 Восстановление из {selected_backup}...")
    if restore_backup(selected_backup):
        print("\n✅ ВОССТАНОВЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("База данных восстановлена из резервной копии")
    else:
        print("\n❌ ОШИБКА ПРИ ВОССТАНОВЛЕНИИ!")

if __name__ == "__main__":
    main()
