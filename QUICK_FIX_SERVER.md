# Быстрое исправление базы данных на сервере

## 🚨 База данных повреждена - срочное исправление

### Шаг 1: Остановите бота

```bash
sudo systemctl stop judges-bot
```

### Шаг 2: Загрузите скрипты на сервер

Загрузите эти файлы на сервер в `/root/judges_bot_v2/`:
- `diagnose_database.py`
- `safe_repair_database.py`
- `repair_database.py`

### Шаг 3: Удалите WAL файлы

```bash
cd /root/judges_bot_v2
rm -f bot_database.db-wal bot_database.db-shm bot_database.db-journal
```

### Шаг 4: Проверьте базу данных

```bash
python3 diagnose_database.py
```

### Шаг 5: Восстановите базу данных

```bash
python3 safe_repair_database.py
```

Если не помогло:

```bash
python3 repair_database.py
```

### Шаг 6: Если восстановление не удалось - используйте резервную копию

```bash
# Найдите последнюю резервную копию
ls -lah bot_database.db.backup*

# Восстановите из резервной копии
cp bot_database.db.backup_YYYYMMDD_HHMMSS bot_database.db

# Удалите WAL файлы
rm -f bot_database.db-wal bot_database.db-shm

# Проверьте целостность
sqlite3 bot_database.db "PRAGMA integrity_check;"
```

### Шаг 7: Запустите бота

```bash
sudo systemctl start judges-bot
sudo systemctl status judges-bot
```

### Шаг 8: Проверьте логи

```bash
sudo journalctl -u judges-bot -n 50 --no-pager
```

## 🔍 Если проблема повторяется

1. **Проверьте место на диске:**
```bash
df -h
```

2. **Проверьте диск на ошибки:**
```bash
dmesg | grep -i error
```

3. **Отключите WAL режим** (временно):
   - Измените `database.py` на сервере
   - Замените `PRAGMA journal_mode = WAL;` на `PRAGMA journal_mode = DELETE;`
   - Перезапустите бота

