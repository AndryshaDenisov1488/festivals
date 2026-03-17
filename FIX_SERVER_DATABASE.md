# Исправление проблем с данными на сервере

## 📋 Что нужно исправить:

1. **Неправильные суммы заработка** (31 запись)
2. **Записи для неутвержденных регистраций** (54 записи)
3. **Неоплаченные записи** (150 записей)

## 🚀 Пошаговая инструкция:

### Шаг 1: Остановите бота

```bash
sudo systemctl stop judges-bot
```

### Шаг 2: Загрузите скрипты на сервер

Загрузите эти файлы на сервер в `/root/judges_bot_v2/`:
- `fix_all_database_issues.py`
- `check_database_comprehensive.py`
- `mass_update_payments.py` (опционально, если нужно массовое обновление)

**Через scp:**
```bash
scp fix_all_database_issues.py root@your_server_ip:/root/judges_bot_v2/
scp check_database_comprehensive.py root@your_server_ip:/root/judges_bot_v2/
scp mass_update_payments.py root@your_server_ip:/root/judges_bot_v2/
```

### Шаг 3: Создайте резервную копию базы данных

```bash
cd /root/judges_bot_v2
cp bot_database.db bot_database.db.backup_before_fix_$(date +%Y%m%d_%H%M%S)
```

### Шаг 4: Проверьте текущее состояние

```bash
python3 check_database_comprehensive.py
```

Это покажет все проблемы, которые нужно исправить.

### Шаг 5: Проверьте, что будет исправлено (режим проверки)

```bash
python3 fix_all_database_issues.py
```

Скрипт покажет:
- Какие записи будут удалены
- Какие суммы будут исправлены
- Какие неоплаченные записи будут обновлены

**Внимательно проверьте вывод!**

### Шаг 6: Примените исправления

```bash
python3 fix_all_database_issues.py --apply
```

Скрипт выполнит:
1. ✅ Удалит записи об оплате для неутвержденных/удаленных регистраций
2. ✅ Исправит некорректные суммы (5000 для всех, 7000 для Лизочки Марковой)
3. ✅ Обновит неоплаченные записи (пометить как оплаченные с правильными суммами)

### Шаг 7: Проверьте результат

```bash
python3 check_database_comprehensive.py
```

Все проблемы должны быть исправлены.

### Шаг 8: Удалите WAL файлы (важно!)

```bash
rm -f bot_database.db-wal bot_database.db-shm bot_database.db-journal
```

### Шаг 9: Запустите бота

```bash
sudo systemctl start judges-bot
sudo systemctl status judges-bot
```

### Шаг 10: Проверьте логи

```bash
sudo journalctl -u judges-bot -n 50 --no-pager
```

## ⚠️ Важно:

1. **Всегда создавайте резервную копию** перед исправлениями
2. **Сначала запускайте в режиме проверки** (без `--apply`)
3. **Удаляйте WAL файлы** после исправлений
4. **Проверяйте результат** после исправлений

## 🔄 Если что-то пошло не так:

```bash
# Восстановите из резервной копии
cd /root/judges_bot_v2
cp bot_database.db.backup_before_fix_YYYYMMDD_HHMMSS bot_database.db
rm -f bot_database.db-wal bot_database.db-shm
sudo systemctl restart judges-bot
```

## 📊 Что делает скрипт fix_all_database_issues.py:

1. **Удаляет записи для неутвержденных регистраций:**
   - Записи об оплате для судей, которые отменили регистрацию
   - Записи для судей со статусом REJECTED или PENDING

2. **Исправляет некорректные суммы:**
   - Для обычных судей: устанавливает 5000 руб.
   - Для Лизочки Марковой (ID: 946719504): устанавливает 7000 руб.
   - Исправляет суммы меньше 3500 руб.
   - Исправляет суммы, которые не равны стандартным

3. **Обновляет неоплаченные записи:**
   - Помечает как оплаченные
   - Устанавливает правильные суммы (5000 или 7000)
   - Устанавливает дату оплаты

