@echo off
REM Скрипт для загрузки файлов и запуска бота на сервере (Windows)

echo 🚀 ЗАГРУЗКА И ЗАПУСК БОТА
echo ================================

REM Замените на ваши данные сервера
set SERVER_USER=your_username
set SERVER_HOST=your_server_ip
set SERVER_PATH=/path/to/bot

echo 📁 Загружаем файлы на сервер...

REM Основные файлы бота
scp main.py %SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/
scp config.py %SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/
scp models.py %SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/
scp database.py %SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/
scp states.py %SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/
scp keyboards.py %SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/
scp requirements.txt %SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/

REM Папки
scp -r handlers/ %SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/
scp -r services/ %SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/
scp -r utils/ %SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/

REM База данных
scp bot_database.db %SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/

REM Тестовые скрипты
scp test_budget_reminders.py %SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/
scp test_payment_reminders.py %SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/
scp create_payment_records.py %SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/
scp send_payment_reminders_manual.py %SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/
scp send_budget_reminders_manual.py %SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/
scp cleanup_production_db.py %SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/

echo ✅ Загрузка завершена!
echo.
echo 🔧 Теперь подключитесь к серверу и выполните команды:
echo.
echo ssh %SERVER_USER%@%SERVER_HOST%
echo cd %SERVER_PATH%
echo pip install -r requirements.txt
echo python send_payment_reminders_manual.py
echo nohup python main.py ^> bot.log 2^>^&1 ^&
echo.
echo 🎉 Готово!
