#!/usr/bin/env python3
"""
Восстановление БД из бэкапа или из старого проекта.

Использование:
  python restore_database.py path/to/old/bot_database.db
  python restore_database.py path/to/backup.db

Перед восстановлением создаётся бэкап текущей БД.
Копирует также -shm и -wal (SQLite WAL) — в них могут быть последние данные.
"""
import os
import shutil
import sys
from datetime import datetime

from config import DATABASE_URL

def main():
    if len(sys.argv) < 2:
        print("Использование: python restore_database.py <путь_к_файлу_бд>")
        print("Пример: python restore_database.py ../judges_bot_v2_old/bot_database.db")
        sys.exit(1)

    source = os.path.abspath(sys.argv[1])
    if not os.path.exists(source):
        print(f"❌ Файл не найден: {source}")
        sys.exit(1)

    if not DATABASE_URL.startswith("sqlite:///"):
        print(f"❌ Скрипт работает только с SQLite. Текущий DATABASE_URL: {DATABASE_URL}")
        sys.exit(1)

    target = DATABASE_URL.replace("sqlite:///", "").replace("sqlite://", "")
    if not os.path.isabs(target.replace("/", os.sep)):
        target = os.path.join(os.path.dirname(os.path.abspath(__file__)), target)
    target = os.path.normpath(target.replace("/", os.sep))

    target_dir = os.path.dirname(target)
    if os.path.exists(target):
        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir = os.path.join(target_dir, backup_name)
        os.makedirs(backup_dir, exist_ok=True)
        target_base = target
        if target_base.endswith("-shm") or target_base.endswith("-wal"):
            target_base = target_base.rsplit("-", 1)[0]
        for suf in ("", "-shm", "-wal"):
            p = target_base + suf
            if os.path.exists(p):
                shutil.copy2(p, os.path.join(backup_dir, os.path.basename(p)))
        print(f"📦 Бэкап текущей БД: {backup_dir}")

    src_base = source.replace("-shm", "").replace("-wal", "")
    if not src_base.endswith(".db"):
        src_base = source
    else:
        src_base = source[:-3]
    for suf in ("", "-shm", "-wal"):
        src = src_base + (".db" if suf == "" else suf)
        tgt = target + ("" if suf == "" else suf)
        if os.path.exists(src):
            shutil.copy2(src, tgt)
            print(f"   Скопирован: {os.path.basename(src)}")
    if not os.path.exists(target):
        shutil.copy2(source, target)
    print(f"✅ БД восстановлена из {source}")
    print(f"   → {target}")
    print("\nПерезапустите бота и API.")

if __name__ == "__main__":
    main()
