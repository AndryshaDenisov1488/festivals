# Инструкция по загрузке базы данных на сервер

## 📁 Что нужно загрузить

**Загружайте ТОЛЬКО основной файл базы данных:**
- `bot_database.db`

**НЕ загружайте:**
- `bot_database.db-wal` (WAL файл - создается автоматически)
- `bot_database.db-shm` (SHM файл - создается автоматически)
- `bot_database.db-journal` (журнал - создается автоматически)

## 🔧 Процесс загрузки

### 1. Остановите бота на сервере:

```bash
sudo systemctl stop judges-bot
```

### 2. Создайте резервную копию текущей базы на сервере:

```bash
cd /root/judges_bot_v2
cp bot_database.db bot_database.db.backup_$(date +%Y%m%d_%H%M%S)
```

### 3. Загрузите новый файл базы данных:

**С Windows (используя WinSCP, FileZilla или scp):**

```bash
# Через scp из PowerShell или CMD
scp bot_database.db root@your_server_ip:/root/judges_bot_v2/
```

**Или через WinSCP/FileZilla:**
- Подключитесь к серверу
- Перейдите в `/root/judges_bot_v2/`
- Загрузите файл `bot_database.db`

### 4. Удалите WAL файлы на сервере (если они есть):

```bash
cd /root/judges_bot_v2
rm -f bot_database.db-wal bot_database.db-shm bot_database.db-journal
```

**Важно:** WAL файлы могут быть повреждены и вызвать проблемы. Лучше их удалить, чтобы SQLite создал новые.

### 5. Проверьте права доступа:

```bash
chmod 644 bot_database.db
chown root:root bot_database.db
```

### 6. Проверьте базу данных (опционально):

```bash
# Загрузите скрипт проверки на сервер
scp check_database_comprehensive.py root@your_server_ip:/root/judges_bot_v2/

# Запустите проверку
cd /root/judges_bot_v2
python3 check_database_comprehensive.py
```

### 7. Запустите бота:

```bash
sudo systemctl start judges-bot
sudo systemctl status judges-bot
```

### 8. Проверьте логи:

```bash
sudo journalctl -u judges-bot -n 50 --no-pager
```

## ⚠️ Важные моменты

1. **Всегда создавайте резервную копию** перед заменой базы данных
2. **Удаляйте WAL файлы** после загрузки новой базы - они могут быть несовместимы
3. **Проверяйте базу** перед запуском бота
4. **Не загружайте WAL/SHM файлы** - они создаются автоматически при работе

## 🔍 Если возникли проблемы

### База данных повреждена после загрузки:

```bash
# Восстановите из резервной копии
cd /root/judges_bot_v2
cp bot_database.db.backup_YYYYMMDD_HHMMSS bot_database.db
rm -f bot_database.db-wal bot_database.db-shm
sudo systemctl restart judges-bot
```

### Ошибка "database is locked":

```bash
# Убедитесь, что бот остановлен
sudo systemctl stop judges-bot

# Удалите WAL файлы
rm -f bot_database.db-wal bot_database.db-shm

# Запустите бота снова
sudo systemctl start judges-bot
```

## 📝 Автоматическое резервное копирование

Рекомендуется настроить автоматическое резервное копирование:

```bash
# Создайте скрипт резервного копирования
cat > /root/judges_bot_v2/backup_db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/root/judges_bot_v2/backups"
mkdir -p $BACKUP_DIR
cp /root/judges_bot_v2/bot_database.db $BACKUP_DIR/bot_database_$(date +%Y%m%d_%H%M%S).db
find $BACKUP_DIR -name "bot_database_*.db" -mtime +30 -delete
EOF

chmod +x /root/judges_bot_v2/backup_db.sh

# Добавьте в crontab (ежедневно в 2:00)
crontab -e
# Добавьте строку:
0 2 * * * /root/judges_bot_v2/backup_db.sh
```

