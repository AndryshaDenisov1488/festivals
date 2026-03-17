#!/bin/bash
# Скрипт для загрузки файлов на сервер

echo "🚀 ЗАГРУЗКА ФАЙЛОВ НА СЕРВЕР"
echo "================================"

# Замените на ваши данные сервера
SERVER_USER="your_username"
SERVER_HOST="your_server_ip"
SERVER_PATH="/path/to/bot"

# Основные файлы бота
echo "📁 Загружаем основные файлы..."
scp main.py $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
scp config.py $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
scp models.py $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
scp database.py $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
scp states.py $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
scp keyboards.py $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
scp requirements.txt $SERVER_USER@$SERVER_HOST:$SERVER_PATH/

# Папки
echo "📁 Загружаем папки..."
scp -r handlers/ $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
scp -r services/ $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
scp -r utils/ $SERVER_USER@$SERVER_HOST:$SERVER_PATH/

# База данных
echo "📁 Загружаем базу данных..."
scp bot_database.db $SERVER_USER@$SERVER_HOST:$SERVER_PATH/

# Тестовые скрипты
echo "📁 Загружаем тестовые скрипты..."
scp test_budget_reminders.py $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
scp test_payment_reminders.py $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
scp create_payment_records.py $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
scp send_payment_reminders_manual.py $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
scp send_budget_reminders_manual.py $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
scp cleanup_production_db.py $SERVER_USER@$SERVER_HOST:$SERVER_PATH/

echo "✅ Загрузка завершена!"
echo ""
echo "🔧 Команды для запуска на сервере:"
echo "1. Подключитесь к серверу: ssh $SERVER_USER@$SERVER_HOST"
echo "2. Перейдите в папку: cd $SERVER_PATH"
echo "3. Установите зависимости: pip install -r requirements.txt"
echo "4. Запустите бота: python main.py"
echo "5. Для тестирования: python send_payment_reminders_manual.py"
