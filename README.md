# Judges Bot v2

Telegram-бот для судей и веб-интерфейс для работы через сайт.

## Структура

- **Бот** — Telegram-бот (aiogram)
- **API** — FastAPI (порт 8100)
- **Web** — Next.js (порт 3000)

## Локальная разработка

### API

```bash
uvicorn api.main:app --host 127.0.0.1 --port 8100
```

### Web

```bash
cd web
cp .env.example .env.local
# В .env.local: NEXT_PUBLIC_API_URL=http://localhost:8100
npm install
npm run dev
```

Открой http://localhost:3000

## Деплой на сервер

### 1. Требования

- Python 3.10+
- Node.js 18+
- (опционально) nginx

### 2. Установка

```bash
cd ~/judges_bot_v2
git pull

# Python
python -m venv venv
source venv/bin/activate  # Linux: source venv/bin/activate
pip install -r requirements.txt

# Web
cd web
npm install
npm run build
cd ..
```

### 3. Переменные окружения (.env)

Создай файл `.env` в корне проекта:

```env
BOT_TOKEN=...
ADMIN_IDS=123456789
CHANNEL_ID=-100...
DATABASE_URL=sqlite:///bot_database.db

# Для входа в веб (SMTP)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
SMTP_FROM=noreply@example.com

# JWT для API (опционально, по умолчанию CHANGE_ME_SECRET)
JWT_SECRET=your-random-secret
```

### 4. Сборка Web с правильным API URL

Перед `npm run build` задай `NEXT_PUBLIC_API_URL`:

- **С nginx** (веб и API на одном домене, напр. festsfs.ru): `NEXT_PUBLIC_API_URL=""` — запросы идут на `/api/...`
- **Без nginx** (прямой доступ): `NEXT_PUBLIC_API_URL=http://IP_СЕРВЕРА:8100`

```bash
cd web
NEXT_PUBLIC_API_URL="" npm run build   # для nginx
# или
NEXT_PUBLIC_API_URL=http://192.168.1.10:8100 npm run build   # без nginx
```

### 5. Systemd

Скопируй unit-файлы и замени `YOUR_USER` на имя пользователя:

```bash
sudo cp deploy/judges-bot.service /etc/systemd/system/
sudo cp deploy/judges-api.service /etc/systemd/system/
sudo cp deploy/judges-web.service /etc/systemd/system/

# Замени YOUR_USER и путь (для root: /home/root → /root)
sudo sed -i 's/YOUR_USER/your_username/g' /etc/systemd/system/judges-*.service
sudo sed -i 's|/home/your_username|/root|g' /etc/systemd/system/judges-*.service   # если пользователь root
```

Запуск:

```bash
sudo systemctl daemon-reload
sudo systemctl enable judges-bot judges-api judges-web
sudo systemctl start judges-bot judges-api judges-web
sudo systemctl status judges-bot judges-api judges-web
```

### 6. Nginx (опционально)

Если нужен домен и HTTPS:

1. **DNS** — добавь A-запись: `festsfs.ru` → IP сервера
2. **SSL** — после nginx: `sudo apt install certbot python3-certbot-nginx && sudo certbot --nginx -d festsfs.ru`

```bash
sudo cp deploy/nginx.conf.example /etc/nginx/sites-available/judges
sudo ln -s /etc/nginx/sites-available/judges /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 7. Вход в веб

1. Судья привязывает email в боте: главное меню → «Привязать email (для входа на сайт)» → ввести email → получить код на почту → ввести код
2. На странице логина веб-портала ввести email
3. Получить код на почту (проверь SMTP в .env)
4. Ввести код и войти

## API

- `POST /api/v1/auth/request-code` — запрос кода на email
- `POST /api/v1/auth/verify-code` — проверка кода, получение JWT
- `GET /api/v1/users/me` — текущий пользователь
- `GET /api/v1/tournaments` — список турниров
- `GET /api/v1/registrations/my` — мои заявки
- `POST /api/v1/registrations` — подать заявку
- `DELETE /api/v1/registrations/{id}` — отменить заявку
- `GET /api/v1/earnings/my/payments` — список выплат (с payment_id для confirm/correct)
- `GET /api/v1/earnings/my/detail` — детали выплат
- `GET /api/v1/earnings/my/summary` — сводка выплат
- `POST /api/v1/earnings/my/confirm` — подтвердить получение оплаты
- `POST /api/v1/earnings/my/correct` — исправить сумму
- `POST /api/v1/admin/broadcast` — рассылка (только админ)
- `GET /api/v1/admin/registrations` — список заявок
- `POST /api/v1/admin/registrations/{id}/approve` — одобрить заявку
- `POST /api/v1/admin/registrations/{id}/reject` — отклонить заявку
- `GET /api/v1/admin/budgets` — бюджеты турниров
- `GET /api/v1/admin/budgets/summary` — сводка по прибыли
- `GET/POST /api/v1/admin/budgets/{id}` — получить/установить бюджет
- `GET /api/v1/admin/exports/month?month=...` — экспорт Excel по месяцу
- `GET /api/v1/admin/exports/year?year=...` — экспорт Excel по году

Документация: `http://IP:8100/docs`
