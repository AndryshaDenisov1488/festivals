#!/bin/bash
# Скрипт для загрузки файлов и запуска бота на сервере

echo "🚀 ЗАГРУЗКА И ЗАПУСК БОТА"
echo "================================"

# Замените на ваши данные сервера
SERVER_USER="your_username"
SERVER_HOST="your_server_ip"
SERVER_PATH="/path/to/bot"

echo "📁 Загружаем файлы на сервер..."

# Основные файлы бота
scp main.py $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
scp config.py $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
scp models.py $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
scp database.py $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
scp states.py $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
scp keyboards.py $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
scp requirements.txt $SERVER_USER@$SERVER_HOST:$SERVER_PATH/

# Папки
scp -r handlers/ $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
scp -r services/ $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
scp -r utils/ $SERVER_USER@$SERVER_HOST:$SERVER_PATH/

# База данных
scp bot_database.db $SERVER_USER@$SERVER_HOST:$SERVER_PATH/

# Тестовые скрипты
scp test_budget_reminders.py $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
scp test_payment_reminders.py $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
scp create_payment_records.py $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
scp send_payment_reminders_manual.py $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
scp send_budget_reminders_manual.py $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
scp cleanup_production_db.py $SERVER_USER@$SERVER_HOST:$SERVER_PATH/

echo "✅ Загрузка завершена!"
echo ""
echo "🔧 Подключаемся к серверу и запускаем бота..."

# Подключаемся к серверу и запускаем команды
ssh $SERVER_USER@$SERVER_HOST << 'EOF'
cd /path/to/bot

echo "📦 Устанавливаем зависимости..."
pip install -r requirements.txt

echo "🧪 Тестируем напоминания об оплате..."
python send_payment_reminders_manual.py

echo "🚀 Запускаем бота..."
nohup python main.py > bot.log 2>&1 &

echo "✅ Бот запущен в фоновом режиме!"
echo "📋 Логи: tail -f bot.log"
echo "🛑 Остановка: pkill -f main.py"
EOF

echo "🎉 Готово! Бот запущен на сервере!"
