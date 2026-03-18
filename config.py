import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
# Список админов (ID через запятую в .env)
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []
# Канал или чат для уведомлений (например, "-1001234567890" или "@your_channel")
CHANNEL_ID = os.getenv("CHANNEL_ID", "")
# Email админа для уведомлений о новых заявках (опционально)
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")

def validate_config():
    """Валидация конфигурации при запуске"""
    errors = []
    
    if not BOT_TOKEN:
        errors.append("BOT_TOKEN не установлен")
    
    if not ADMIN_IDS:
        errors.append("ADMIN_IDS не установлен")
    
    if not CHANNEL_ID:
        errors.append("CHANNEL_ID не установлен")
    
    if errors:
        raise ValueError(f"Ошибки конфигурации: {', '.join(errors)}")

# Вызываем валидацию при импорте
try:
    validate_config()
except ValueError as e:
    print(f"❌ {e}")
    print("Проверьте файл .env и убедитесь, что все переменные установлены.")
    raise

# Настройки базы данных
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot_database.db")

# Другие настройки
MAX_JUDGES_PER_TOURNAMENT = 15  # По умолчанию 15 судей
MAX_MESSAGE_LENGTH = 4096       # Лимит символов в одном сообщении Telegram

# Веб-портал судей (для ссылок в боте)
WEB_PORTAL_URL = os.getenv("WEB_PORTAL_URL", "https://festsfs.ru")

# Настройки мониторинга
ENABLE_ERROR_MONITORING = True  # Включить мониторинг ошибок