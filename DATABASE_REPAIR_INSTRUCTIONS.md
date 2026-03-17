# Инструкция по восстановлению поврежденной базы данных

## ⚠️ ПРОБЛЕМА: База данных повреждена

Если вы видите ошибку `database disk image is malformed`, база данных SQLite повреждена и требует восстановления.

## 🔧 ШАГИ ПО ВОССТАНОВЛЕНИЮ

### 1. Остановите бота

```bash
sudo systemctl stop judges-bot
```

### 2. Создайте резервную копию

```bash
cd /root/judges_bot_v2
cp bot_database.db bot_database.db.backup_$(date +%Y%m%d_%H%M%S)
```

### 3. Загрузите скрипт восстановления на сервер

Загрузите файл `repair_database.py` на сервер в директорию `/root/judges_bot_v2/`

### 4. Запустите скрипт восстановления

```bash
cd /root/judges_bot_v2
python3 repair_database.py
```

Скрипт автоматически:
- Проверит целостность базы данных
- Создаст резервную копию
- Попытается восстановить базу данных

### 5. Если скрипт не помог, попробуйте вручную

```bash
# Метод 1: Использование sqlite3 .recover (требует sqlite3 3.38+)
sqlite3 bot_database.db ".recover" | sqlite3 bot_database_repaired.db

# Проверьте восстановленную базу
sqlite3 bot_database_repaired.db "PRAGMA integrity_check;"

# Если все ок, замените старую базу
mv bot_database_repaired.db bot_database.db
```

### 6. Если восстановление не удалось

Если у вас есть резервная копия базы данных:

```bash
# Найдите последнюю резервную копию
ls -lah bot_database.db.backup*

# Восстановите из резервной копии
cp bot_database.db.backup_YYYYMMDD_HHMMSS bot_database.db
```

### 7. После восстановления запустите бота

```bash
sudo systemctl start judges-bot
sudo systemctl status judges-bot
```

### 8. Проверьте логи

```bash
sudo journalctl -u judges-bot -n 50 --no-pager
```

## 🔍 ПРИЧИНЫ ПОВРЕЖДЕНИЯ БАЗЫ ДАННЫХ

1. **Неожиданное завершение работы** - бот был остановлен во время записи
2. **Нехватка места на диске** - проверьте свободное место: `df -h`
3. **Проблемы с диском** - проверьте диск: `dmesg | grep -i error`
4. **Одновременный доступ** - несколько процессов пытаются писать одновременно

## 💡 ПРОФИЛАКТИКА

1. **Регулярные резервные копии** - создавайте резервные копии базы данных ежедневно
2. **Мониторинг места на диске** - следите за свободным местом
3. **Правильное завершение работы** - всегда останавливайте бота через systemctl

## 📝 СКРИПТ ДЛЯ АВТОМАТИЧЕСКОГО РЕЗЕРВНОГО КОПИРОВАНИЯ

Создайте файл `/root/judges_bot_v2/backup_db.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/root/judges_bot_v2/backups"
mkdir -p $BACKUP_DIR
cp /root/judges_bot_v2/bot_database.db $BACKUP_DIR/bot_database_$(date +%Y%m%d_%H%M%S).db
# Удаляем старые резервные копии (старше 30 дней)
find $BACKUP_DIR -name "bot_database_*.db" -mtime +30 -delete
```

Добавьте в crontab для ежедневного резервного копирования:

```bash
crontab -e
# Добавьте строку:
0 2 * * * /root/judges_bot_v2/backup_db.sh
```

