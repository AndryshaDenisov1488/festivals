# Judges Bot v2

<p align="center">
  <strong>Экосистема для судей: Telegram-бот, FastAPI, Next.js веб-портал, заявки, выплаты, бюджеты</strong>
</p>

<p align="center">
  <a href="https://festsfs.ru">festsfs.ru</a> ·
  <a href=".cursor/skills/judges-bot-v2/reference.md">Полная документация (Ultra)</a> ·
  <a href=".cursor/skills/judges-bot-v2/SKILL.md">AI Skill</a>
</p>

---

## Содержание

1. [О проекте](#о-проекте)
2. [Ключевые возможности](#ключевые-возможности)
3. [Архитектура](#архитектура)
4. [Технологический стек](#технологический-стек)
5. [Структура репозитория](#структура-репозитория)
6. [API](#api)
7. [База данных](#база-данных)
8. [Установка и разработка](#установка-и-разработка)
9. [Деплой на production](#деплой-на-production)
10. [Конфигурация (.env)](#конфигурация-env)
11. [Мониторинг и логи](#мониторинг-и-логи)
12. [Бэкапы](#бэкапы)
13. [Безопасность](#безопасность)
14. [Интеграции](#интеграции)
15. [Документация](#документация)

---

## О проекте

**Judges Bot v2** — Экосистема для судей: Telegram-бот, FastAPI, Next.js веб-портал, заявки, выплаты, бюджеты.

Система является частью экосистемы **ФФКМ** и развёрнута на production-сервере:

| | |
|--|--|
| Сервер | xkvlorcrjx (45.12.237.105, Beget VPS) |
| ОС | Ubuntu 22.04.5 LTS |
| URL | https://festsfs.ru |
| Backend | 127.0.0.1:3000 (Next.js), 8101 (API) |
| БД | SQLite: bot_database.db |
| Systemd | judges-bot, judges-api, judges-web |
| Unix user | root |
| Интеграции | — |

### Расположение на сервере

| Параметр | Значение |
|----------|----------|
| Путь | `/root/judges_bot_v2` |
| Домен | `festsfs.ru` |
| Порт backend | `3000 (Next.js), 8101 (API)` |
| Systemd | `judges-bot, judges-api, judges-web` |
| Пользователь | `root` |
| БД | `SQLite: bot_database.db` |

---

## Ключевые возможности

# Pirates [![Coverage][codecov-badge]][codecov-link]

### Properly hijack require

This library allows to add custom require hooks, which do not interfere with other require hooks.

This library only works with commonJS.

[codecov-badge]: https://img.shields.io/codecov/c/github/danez/pirates/master.svg?style=flat "codecov"
[codecov-link]: https://codecov.io/gh/danez/pirates "codecov"

## Why?

Two reasons:
1. Babel and istanbul were breaking each other.
2. Everyone seemed to re-invent the wheel on this, and everyone wanted a solution that was DRY, simple, easy to use,
and made everything Just Work™, while allowing multiple require hooks, in a fashion similar to calling `super`.

For some context, see [the Babel issue thread][] which started this all, then [the nyc issue thread][], where
discussion was moved (as we began to discuss just using the code nyc had developed), and finally to [#1][issue-1]
where discussion was finally moved.

[the Babel issue thread]: https://github.com/babel/babel/pull/3062 "Babel Issue Thread"
[the nyc issue thread]: https://github.com/bcoe/nyc/issues/70 "NYC Issue Thread"
[issue-1]: https://github.com/danez/pirates/issues/1 "Issue #1"

## Installation

    npm install --save pirates

## Usage

Using pirates is really easy:
```javascript
// my-module/register.js
const addHook = require('pirates').addHook;
// Or if you use ES modules
// import { addHook } from 'pirates';

function matcher(filename) {
  // Here, you can inspect the filename to determine if it should be hooked or
  // not. Just return a truthy/falsey. Files in node_modules are automatically ignored,
  // unless otherwise specified in options (see below).

  // TODO: Implement your logic here
  return true;
}

const revert = addHook(
  (code, filename) => code.replace('@@foo', 'console.log(\'foo\');'),
  { exts: ['.js'], matcher }
);

// And later, if you want to un-hook require, you can just do:
revert();
```

## API

### pirates.addHook(hook, [opts={ [matcher: true], [exts: ['.js']], [ignoreNodeModules: true] }]);
Add a require hook. `hook` must be a function that takes `(code, filename)`, and returns the modified code. `opts` is
an optional options object. Available options are: `matcher`, which is a function that accepts a filename, and
returns a truthy value if the file should be hooked (defaults to a function that always returns true), falsey if
otherwise; `exts`, which is an array of extensions to hook, they should begin with `.` (defaults to `['.js']`);
`ignoreNodeModules`, if true, any file in a `node_modules` folder wont be hooked (the matcher also wont be called),
if false, then the matcher will be called for any files in `node_modules` (defaults to true).


## Projects that use Pirates

See the [wiki page](https://github.com/danez/pirates/wiki/Projects-using-Pirates). If you add Pirates to your project,
(And you should! It works best if everyone uses it. Then we can have a happy world full of happy require hooks!), please
add yourself to the wiki.

---

## Архитектура

## 1.1 Описание продукта

**Judges Bot v2** — Экосистема для судей: Telegram-бот, FastAPI, Next.js веб-портал, заявки, выплаты, бюджеты.

Система является частью экосистемы **ФФКМ** и развёрнута на production-сервере:

| | |
|--|--|
| Сервер | xkvlorcrjx (45.12.237.105, Beget VPS) |
| ОС | Ubuntu 22.04.5 LTS |
| URL | https://festsfs.ru |
| Backend | 127.0.0.1:3000 (Next.js), 8101 (API) |
| БД | SQLite: bot_database.db |
| Systemd | judges-bot, judges-api, judges-web |
| Unix user | root |
| Интеграции | — |

## 1.2

```
Интернет → nginx (443) → 127.0.0.1:3000 (Next.js) → systemd (judges-bot, judges-api, judges-web)
```

---

## Технологический стек

ЗАВИСИМОСТИ И СТЕК

## 2.1 Python зависимости

```
SQLAlchemy
aiogram
aiosqlite
alembic
apscheduler
bcrypt>=4.0.0,<4.1.0
fastapi
openpyxl
passlib
python-dotenv
python-jose
pytz
uvicorn
```

## 2.2 JavaScript зависимости

```json
{
  "dependencies": {
    "next": "^14.2.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@radix-ui/react-slot": "^1.0.2",
    "@radix-ui/react-label": "^2.0.2",
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-dropdown-menu": "^2.0.6",
    "@radix-ui/react-avatar": "^1.0.4",
    "@radix-ui/react-separator": "^1.0.3",
    "@radix-ui/react-tabs": "^1.0.4",
    "@radix-ui/react-toast": "^1.1.5",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "lucide-react": "^0.400.0",
    "tailwind-merge": "^2.2.0"
  },
  "devDependencies": {
    "tailwindcss-animate": "^1.0.7",
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "autoprefixer": "^10.0.1",
    "eslint": "^8",
    "eslint-config-next": "^14.2.0",
    "postcss": "^8",
    "tailwindcss": "^3.4.1",
    "typescript": "^5"
  }
}
```

---

---

## Структура репозитория

```
.
./backups
./api
./api/schemas
./api/schemas/__pycache__
./api/__pycache__
./api/routers
./api/routers/__pycache__
./backup_20260318_123846
./.cursor
./.cursor/skills
./.cursor/skills/judges-bot-v2
./alembic
./alembic/__pycache__
./alembic/versions
./alembic/versions/__pycache__
./tests
./__pycache__
./handlers
./handlers/__pycache__
./web
./web/.next
./web/.next/standalone
./web/.next/types
./web/.next/server
./web/.next/static
./web/.next/cache
./web/src
./web/src/components
./web/src/lib
./web/src/app
./web/scripts
./web/node_modules
./web/node_modules/pirates
./web/node_modules/update-browserslist-db
./web/node_modules/reflect.getprototypeof
./web/node_modules/node-exports-info
./web/node_modules/imurmurhash
./web/node_modules/@eslint
./web/node_modules/didyoumean
./web/node_modules/@rushstack
./web/node_modules/tailwind-merge
./web/node_modules/levn
./web/node_modules/available-typed-arrays
./web/node_modules/json-schema-traverse
./web/node_modules/optionator
./web/node_modules/lodash.merge
./web/node_modules/client-only
./web/node_modules/get-intrinsic
./web/node_modules/sucrase
./web/node_modules/string.prototype.includes
./web/node_modules/eslint-plugin-import
./web/node_modules/prelude-ls
./web/node_modules/jiti
./web/node_modules/is-weakset
./web/node_modules/is-string
./web/node_modules/tailwindcss-animate
./web/node_modules/espree
./web/node_modules/fastq
./web/node_modules/gopd
./web/node_modules/eslint-import-resolver-typescript
./web/node_modules/signal-exit
./web/node_modules/json5
./web/node_modules/unbox-primitive
./web/node_modules/is-async-function
./web/node_modules/autoprefixer
./web/node_modules/concat-map
./web/node_modules/is-typed-array
./web/node_modules/esutils
./web/node_modules/side-channel-map
./web/node_modules/iterator.prototype
./web/node_modules/@emnapi
./web/node_modules/stable-hash
./web/node_modules/clsx
./web/node_modules/get-nonce
./web/node_modules/import-fresh
./web/node_modules/is-glob
./web/node_modules/js-tokens
./web/node_modules/path-exists
./web/node_modules/napi-postinstall
```

Полный каталог: [reference.md § Часть III](.cursor/skills/judges-bot-v2/reference.md)

---

## API

И МАРШРУТЫ (ПОЛНЫЙ РЕЕСТР)

Всего: **35** endpoints

```
POST /broadcast  ← `api/routers/admin.py`
GET /registrations  ← `api/routers/admin.py`
GET /registrations/refusals-stats  ← `api/routers/admin.py`
POST /registrations/{registration_id}/approve  ← `api/routers/admin.py`
POST /registrations/{registration_id}/reject  ← `api/routers/admin.py`
GET /users  ← `api/routers/admin.py`
PATCH /users/{user_id}  ← `api/routers/admin.py`
GET /tournaments  ← `api/routers/admin.py`
POST /tournaments  ← `api/routers/admin.py`
PATCH /tournaments/{tournament_id}  ← `api/routers/admin.py`
GET /earnings  ← `api/routers/admin.py`
PATCH /earnings/payment/{payment_id}  ← `api/routers/admin.py`
POST /earnings/request  ← `api/routers/admin.py`
DELETE /tournaments/{tournament_id}  ← `api/routers/admin.py`
POST /request-code  ← `api/routers/auth.py`
POST /verify-code  ← `api/routers/auth.py`
POST /login  ← `api/routers/auth.py`
POST /set-password  ← `api/routers/auth.py`
POST /change-password  ← `api/routers/auth.py`
GET /summary  ← `api/routers/budgets.py`
GET /{tournament_id}  ← `api/routers/budgets.py`
POST /{tournament_id}  ← `api/routers/budgets.py`
GET /month  ← `api/routers/exports.py`
GET /year  ← `api/routers/exports.py`
GET /earnings/my/payments  ← `api/routers/payments.py`
GET /earnings/my/detail  ← `api/routers/payments.py`
GET /earnings/my/summary  ← `api/routers/payments.py`
POST /earnings/my/confirm  ← `api/routers/payments.py`
POST /earnings/my/correct  ← `api/routers/payments.py`
GET /my  ← `api/routers/registrations.py`
DELETE /{registration_id}  ← `api/routers/registrations.py`
GET /{tournament_id}/approved-judges  ← `api/routers/tournaments.py`
GET /{tournament_id}  ← `api/routers/tournaments.py`
GET /me  ← `api/routers/users.py`
PATCH /me  ← `api/routers/users.py`
```

---

---

## База данных

SQLite: bot_database.db

Схема: [reference.md Часть VII](.cursor/skills/judges-bot-v2/reference.md)

---

## Установка и разработка

### Требования

- Python 3.10+ / Node.js 18+ (см. проект)
- SQLite / PostgreSQL (см. конфиг)
- nginx (production)

### Локальный запуск

```bash
git clone <repo>
cd judges_bot_v2
cp env.example .env   # настроить
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# или: cd backend && pip install -r requirements.txt
# Frontend: cd frontend && npm ci && npm run dev
```

---

## Деплой на production

ОПЕРАЦИИ

## Деплой
```bash
cd /root/judges_bot_v2
git pull
# pip install / npm ci / build / migrate
systemctl restart judges-bot
systemctl restart judges-api
systemctl restart judges-web
```

## Диагностика
```bash
systemctl status judges-bot
systemctl status judges-api
systemctl status judges-web
journalctl -u judges-bot -n 200 --no-pager
curl -s http://127.0.0.1:<port>/health
```

## Бэкапы
- Cron 04:00: `/usr/local/sbin/ffkm-project-backups.sh`
- Лог: `/var/log/ffkm-project-backups.log`

---

### ТЗ сервера

# ТЗ: размещение на сервере — Judges Bot v2

## Назначение
Система для работы судей фигурного катания: Telegram-бот на **aiogram**, публичное **веб-приложение (Next.js)** и **REST API (FastAPI)** для сайта и интеграций. Обработка заявок/турниров, уведомления, оплата/бюджет (см. код в `handlers/`, `api/`, БД SQLite).

## Путь на сервере
`/root/judges_bot_v2`

## Systemd-сервисы
| Юнит | Роль |
|------|------|
| `judges-bot.service` | Telegram-бот: `venv/bin/python -m main` |
| `judges-api.service` | FastAPI: `uvicorn api.main:app --host 0.0.0.0 --port 8101` |
| `judges-web.service` | Next.js standalone: `node .next/standalone/server.js`, `PORT=3000` |

## Сеть и домены
- **Публичный сайт/API (nginx):** `festsfs.ru`, `www.festsfs.ru` → HTTPS.
  - `/` → прокси на `127.0.0.1:3000` (фронт).
  - `/api/` → прокси на `127.0.0.1:8101` (бэкенд).
- Конфиг nginx: `/etc/nginx/sites-available/judges` → `sites-enabled/judges`.

⚠️ API слушает **0.0.0.0:8101** — снаружи доступ ограничен firewall/nginx; желательно в будущем привязать только к localhost и проксировать только через nginx.

## Данные и конфигурация
- SQLite: **`bot_database.db`** (рабочая БД), лог **`bot.log`**, см. также `database.py`, `models.py`.
- Секреты и токены: **`.env`** в корне (не коммитить). Для веба — при необходимости `web/.env.local`.
- Alembic: `alembic/`, `alembic.ini` для миграций.

## Логи и диагностика
```bash
journalctl -u judges-bot.service -f
journalctl -u judges-api.service -f
journalctl -u judges-web.service -f
nginx -t && systemctl reload nginx
```

## Зависимости от инфраструктуры
- Отдельная БД PostgreSQL сервера **не требуется** (SQLite).
- Nginx для TLS и маршрутизации.


---

## Конфигурация (.env)

Переменные — в `env.example`. **Никогда не коммитить `.env`.**

На production: `chmod 600 .env`

Полный список: [reference.md Часть VI](.cursor/skills/judges-bot-v2/reference.md)

---

## Мониторинг и логи

```bash
journalctl -u judges-bot -f
systemctl status judges-bot judges-api judges-web
```

Prometheus exporters на сервере: node_exporter, nginx_exporter, postgres_exporter.

---

## Бэкапы

- **Расписание:** ежедневно 04:00 MSK
- **Скрипт:** `/usr/local/sbin/ffkm-project-backups.sh`
- **Лог:** `/var/log/ffkm-project-backups.log`
- **Ротация:** 7 дней

---

## Безопасность

- Backend слушает только `127.0.0.1`
- SSL через Let's Encrypt (certbot)
- UFW + Fail2ban на сервере
- `.env` права 600
- nginx блокирует `/.env`, `/.git`
- Аудит: `/root/server_audit_report_2026-06-10.docx`

---

## Интеграции

—

---

## Документация

| Документ | Описание | Размер |
|----------|----------|--------|
| [reference.md](.cursor/skills/judges-bot-v2/reference.md) | Исчерпывающая техдокументация | ~1200K символов |
| [SKILL.md](.cursor/skills/judges-bot-v2/SKILL.md) | Навигация для AI-агента | — |
| [ТЗ-сервер.md](ТЗ-сервер.md) | ТЗ размещения | — |
| [ffkm-server](/root/.cursor/skills/ffkm-server/) | Документация всего сервера | — |

---


---

## Детальный анализ файлов (выдержка)

### Файл: `README.md`

| Свойство | Значение |
|----------|----------|
| Строк | 447 |
| Размер | 16,028 байт |

### Файл: `alembic.ini`

| Свойство | Значение |
|----------|----------|
| Строк | 37 |
| Размер | 528 байт |

### Файл: `alembic/env.py`

| Свойство | Значение |
|----------|----------|
| Строк | 61 |
| Размер | 1,527 байт |
| Функции | 2 |

**Функции верхнего уровня:**

- `run_migrations_offline()` L29
- `run_migrations_online()` L42

### Файл: `api/__init__.py`

| Свойство | Значение |
|----------|----------|
| Строк | 46 |
| Размер | 2,030 байт |
| Функции | 1 |

**Функции верхнего уровня:**

- `create_app()` L13

### Файл: `api/dependencies.py`

| Свойство | Значение |
|----------|----------|
| Строк | 62 |
| Размер | 1,754 байт |
| Классы | 1 |
| Функции | 3 |

**Классы:**

- `TokenPayload` (строка 19)

**Функции верхнего уровня:**

- `get_db()` L23
- `get_current_user(credentials, db)` L34
- `get_current_admin(user)` L57

### Файл: `api/email_service.py`

| Свойство | Значение |
|----------|----------|
| Строк | 382 |
| Размер | 20,274 байт |
| Функции | 12 |

**Функции верхнего уровня:**

- `_base_html(title, content, accent_color)` L19
- `send_email(to, subject, text, html)` L62
- `send_login_code_email(email, code)` L96
- `send_registration_approved_email(email, tournament_name, tournament_date)` L118
- `send_registration_rejected_email(email, tournament_name, tournament_date)` L146
- `send_new_registration_to_admin_email(admin_email, user_name, tournament_str)` L174
- `send_payment_reminder_email(email, user_name, tournament_name, tournament_date, is_repeat)` L205
- `send_tournament_added_email(email, tournament_name, tournament_date, tournament_month)` L240
- `send_tournament_changed_email(email, tournament_name, tournament_date, changes)` L259
- `send_tournament_deleted_email(email, tournament_name, tournament_month)` L287
- `send_earnings_request_email(email, user_name, tournaments)` L306
- `send_tournament_reminder_email(email, tournament_name, tournament_date)` L355

### Файл: `api/main.py`

| Свойство | Значение |
|----------|----------|
| Строк | 24 |
| Размер | 439 байт |
| Функции | 1 |

**Функции верхнего уровня:**

- `get_application()` L7

### Файл: `api/routers/admin.py`

| Свойство | Значение |
|----------|----------|
| Строк | 917 |
| Размер | 35,196 байт |
| Маршруты | 14 |
| Классы | 6 |
| Функции | 21 |

**Классы:**

- `BroadcastIn` (строка 48)
- `AdminUserUpdateIn` (строка 52)
- `TournamentCreateIn` (строка 60)
- `TournamentUpdateIn` (строка 66)
- `EarningsRequestIn` (строка 771)
- `AdminPaymentAmountIn` (строка 775)

**Функции верхнего уровня:**

- `_get_current_season_start()` L30
- `_get_current_season_end()` L37
- `_get_responsibility_label(refusal_pct)` L44
- `broadcast(payload, admin)` L73
- `admin_list_registrations(month, status, future_only, search, admin)` L99
- `admin_registration_refusals_stats(admin)` L152
- `_notify_judge_approve(user_id, tournament_name, tournament_date)` L242
- `_notify_judge_reject(user_id, tournament_name, tournament_date)` L261
- `admin_approve_registration(registration_id, admin)` L281
- `admin_reject_registration(registration_id, admin)` L339
- `admin_list_users(search, admin)` L379
- `admin_update_user(user_id, payload, admin)` L472
- `admin_list_tournaments(month, future_only, search, admin)` L502
- `_month_from_date(d)` L538
- `admin_create_tournament(payload, admin)` L544
- `_notify_tournament_change(old_name, old_date, old_month, new_name, new_date, new_month)` L595
- `admin_update_tournament(tournament_id, payload, admin)` L650
- `admin_earnings_list(future_only, search, admin)` L681
- `admin_set_payment_amount(payment_id, payload, admin)` L780
- `admin_earnings_request(payload, admin)` L815
- `admin_delete_tournament(tournament_id, admin)` L882

**Маршруты:**
```
POST /broadcast
GET /registrations
GET /registrations/refusals-stats
POST /registrations/{registration_id}/approve
POST /registrations/{registration_id}/reject
GET /users
PATCH /users/{user_id}
GET /tournaments
POST /tournaments
PATCH /tournaments/{tournament_id}
GET /earnings
PATCH /earnings/payment/{payment_id}
POST /earnings/request
DELETE /tournaments/{tournament_id}
```


### Файл: `api/routers/auth.py`

| Свойство | Значение |
|----------|----------|
| Строк | 165 |
| Размер | 7,372 байт |
| Маршруты | 5 |
| Функции | 7 |

**Функции верхнего уровня:**

- `_generate_code(length)` L23
- `_normalize_email(email)` L27
- `request_code(payload)` L32
- `verify_code(payload)` L58
- `login(payload)` L92
- `set_password(payload, user)` L128
- `change_password(payload, user)` L142

**Маршруты:**
```
POST /request-code
POST /verify-code
POST /login
POST /set-password
POST /change-password
```


### Файл: `api/routers/budgets.py`

| Свойство | Значение |
|----------|----------|
| Строк | 81 |
| Размер | 2,316 байт |
| Маршруты | 3 |
| Классы | 1 |
| Функции | 4 |

**Классы:**

- `BudgetSetIn` (строка 64)

**Функции верхнего уровня:**

- `list_budgets(month, future_only, admin)` L18
- `budget_summary(admin)` L44
- `get_budget(tournament_id, admin)` L53
- `set_budget(tournament_id, payload, admin)` L69

**Маршруты:**
```
GET /summary
GET /{tournament_id}
POST /{tournament_id}
```


### Файл: `api/routers/exports.py`

| Свойство | Значение |
|----------|----------|
| Строк | 70 |
| Размер | 2,077 байт |
| Маршруты | 2 |
| Классы | 1 |
| Функции | 2 |

**Классы:**

- `FakeCb` (строка 28)

**Функции верхнего уровня:**

- `export_month(month, admin)` L13
- `export_year(year, admin)` L53

**Маршруты:**
```
GET /month
GET /year
```


### Файл: `api/routers/payments.py`

| Свойство | Значение |
|----------|----------|
| Строк | 180 |
| Размер | 5,942 байт |
| Маршруты | 5 |
| Классы | 2 |
| Функции | 6 |

**Классы:**

- `ConfirmPaymentIn` (строка 123)
- `CorrectEarningsIn` (строка 154)

**Функции верхнего уровня:**

- `get_db()` L17
- `earnings_payments_list(month, future_only, search, user)` L26
- `earnings_detail(user)` L66
- `earnings_summary(user)` L91
- `confirm_payment(payload, user)` L129
- `correct_earnings(payload, user)` L160

**Маршруты:**
```
GET /earnings/my/payments
GET /earnings/my/detail
GET /earnings/my/summary
POST /earnings/my/confirm
POST /earnings/my/correct
```


### Файл: `api/routers/registrations.py`

| Свойство | Значение |
|----------|----------|
| Строк | 202 |
| Размер | 7,407 байт |
| Маршруты | 2 |
| Классы | 1 |
| Функции | 6 |

**Классы:**

- `RegistrationCreateIn` (строка 20)

**Функции верхнего уровня:**

- `my_registrations(month, status, future_only, search, db, user)` L25
- `_notify_channel_new_registration(user_name, tournament_str)` L67
- `_notify_channel_cancel_registration(user_name, tournament_str, previous_status)` L89
- `_notify_admin_email_new_registration(user_name, tournament_str)` L111
- `create_registration(payload, db, user)` L123
- `cancel_registration(registration_id, db, user)` L168

**Маршруты:**
```
GET /my
DELETE /{registration_id}
```


### Файл: `api/routers/tournaments.py`

| Свойство | Значение |
|----------|----------|
| Строк | 124 |
| Размер | 4,174 байт |
| Маршруты | 2 |
| Функции | 3 |

**Функции верхнего уровня:**

- `list_tournaments(month, future_only, from_date, to_date, search, my_approved_only, db, user)` L18
- `list_approved_judges_for_tournament(tournament_id, db, user)` L65
- `get_tournament(tournament_id, db, user)` L110

**Маршруты:**
```
GET /{tournament_id}/approved-judges
GET /{tournament_id}
```


### Файл: `api/routers/users.py`

| Свойство | Значение |
|----------|----------|
| Строк | 42 |
| Размер | 1,305 байт |
| Маршруты | 2 |
| Функции | 2 |

**Функции верхнего уровня:**

- `get_me(user)` L14
- `update_me(payload, user)` L28

**Маршруты:**
```
GET /me
PATCH /me
```


### Файл: `api/schemas/auth.py`

| Свойство | Значение |
|----------|----------|
| Строк | 54 |
| Размер | 1,138 байт |
| Классы | 7 |

**Классы:**

- `AuthRequestCodeIn` (строка 5)
- `AuthVerifyCodeIn` (строка 9)
- `AuthLoginIn` (строка 14)
- `AuthSetPasswordIn` (строка 19)
  - `password_min_length(cls, v)` L24
- `AuthChangePasswordIn` (строка 30)
  - `password_min_length(cls, v)` L36
- `TokenOut` (строка 42)
- `LoginToken` (строка 47)

### Файл: `api/schemas/users.py`

| Свойство | Значение |
|----------|----------|
| Строк | 41 |
| Размер | 1,286 байт |
| Классы | 1 |

**Классы:**

- `ProfileUpdateIn` (строка 7)
  - `validate_name(cls, v)` L15
  - `validate_function(cls, v)` L28
  - `validate_category(cls, v)` L36

### Файл: `api/utils.py`

| Свойство | Значение |
|----------|----------|
| Строк | 37 |
| Размер | 1,224 байт |
| Функции | 3 |

**Функции верхнего уровня:**

- `filter_by_search(items, term)` L10
- `format_date(d)` L20
- `format_datetime(dt)` L27

### Файл: `check_users_login.py`

| Свойство | Значение |
|----------|----------|
| Строк | 44 |
| Размер | 2,200 байт |
| Функции | 1 |

**Функции верхнего уровня:**

- `main()` L12

### Файл: `config.py`

| Свойство | Значение |
|----------|----------|
| Строк | 54 |
| Размер | 2,273 байт |
| Функции | 1 |

**Функции верхнего уровня:**

- `validate_config()` L16

### Файл: `create_payment_records.py`

| Свойство | Значение |
|----------|----------|
| Строк | 78 |
| Размер | 3,230 байт |
| Функции | 1 |

**Функции верхнего уровня:**

- `create_payment_records()` L14

### Файл: `database.py`

| Свойство | Значение |
|----------|----------|
| Строк | 64 |
| Размер | 2,241 байт |
| Функции | 1 |

**Функции верхнего уровня:**

- `_is_sqlite(url)` L9

### Файл: `delete_tournament_force.py`

| Свойство | Значение |
|----------|----------|
| Строк | 204 |
| Размер | 8,678 байт |
| Функции | 1 |

**Функции верхнего уровня:**

- `delete_tournament_force(tournament_name, tournament_date, tournament_id)` L15

### Файл: `deploy/judges-api.service`

| Свойство | Значение |
|----------|----------|
| Строк | 16 |
| Размер | 367 байт |

### Файл: `deploy/judges-bot.service`

| Свойство | Значение |
|----------|----------|
| Строк | 16 |
| Размер | 327 байт |

### Файл: `deploy/judges-web.service`

| Свойство | Значение |
|----------|----------|
| Строк | 17 |
| Размер | 343 байт |

### Файл: `diagnose_database.py`

| Свойство | Значение |
|----------|----------|
| Строк | 211 |
| Размер | 8,534 байт |
| Функции | 4 |

**Функции верхнего уровня:**

- `get_db_path()` L12
- `check_database_health(db_path)` L23
- `fix_wal_files(db_path)` L151
- `main()` L192

### Файл: `fix_all_database_issues.py`

| Свойство | Значение |
|----------|----------|
| Строк | 321 |
| Размер | 13,278 байт |
| Функции | 4 |

**Функции верхнего уровня:**

- `fix_invalid_registration_payments(dry_run)` L24
- `fix_incorrect_amounts(dry_run)` L94
- `fix_unpaid_payments(dry_run)` L169
- `main()` L270

### Файл: `force_send_payment_reminders.py`

| Свойство | Значение |
|----------|----------|
| Строк | 162 |
| Размер | 6,685 байт |
| Функции | 3 |

**Функции верхнего уровня:**

- `send_reminder_to_judge(bot, payment)` L28
- `force_send_reminders()` L67
- `main()` L150

### Файл: `force_send_reminders_simple.py`

| Свойство | Значение |
|----------|----------|
| Строк | 111 |
| Размер | 4,775 байт |
| Функции | 2 |

**Функции верхнего уровня:**

- `show_unpaid_judges()` L18
- `main()` L99

### Файл: `handlers/admin_handlers.py`

| Свойство | Значение |
|----------|----------|
| Строк | 1600 |
| Размер | 76,159 байт |
| Функции | 44 |

**Функции верхнего уровня:**

- `send_tournament_change_notification(bot, users, old_tournament, new_tournament)` L30
- `cmd_admin(message, state)` L92
- `admin_actions(callback_query, state)` L111
- `add_tournament_step(callback_query)` L151
- `process_add_tournament_month(callback_query, state)` L162
- `process_add_tournament_date(message, state)` L175
- `calendar_callbacks(callback_query, state)` L196
- `process_add_tournament_name(message, state)` L325
- `view_referees(callback_query)` L382
- `view_tournaments(callback_query)` L409
- `process_view_tournaments_month(callback_query)` L432
- `edit_tournament_step(callback_query)` L455
- `process_edit_tournament_month(callback_query, state)` L477
- `process_edit_tournament_selection(callback_query, state)` L505
- `process_edit_tournament_new_name(message, state)` L527
- `check_registrations_step(callback_query)` L578
- `process_check_registrations_month(callback_query, state)` L602
- `export_data_step(callback_query)` L641
- `process_export_period(callback_query)` L654
- `select_month_for_export(callback_query)` L672
- `process_export_month(callback_query)` L689
- `select_year_for_export(callback_query)` L695
- `process_export_year(callback_query)` L705
- `delete_tournament_step(callback_query)` L712
- `process_delete_month(cb, state)` L732
- `process_delete_tournament(cb, state)` L756
- `process_delete_confirm(cb, state)` L769
- `admin_sendall_action(callback_query)` L868
- `process_sendall_message(message, state)` L879
- `admin_review_registrations(callback_query)` L912

### Файл: `handlers/budget_handlers.py`

| Свойство | Значение |
|----------|----------|
| Строк | 286 |
| Размер | 14,532 байт |
| Функции | 4 |

**Функции верхнего уровня:**

- `handle_budget_reminder(callback_query, state)` L17
- `process_budget_amount(message, state)` L109
- `show_budget_info(callback_query)` L163
- `show_admin_profit_dashboard(callback_query)` L233

### Файл: `handlers/common_handlers.py`

| Свойство | Значение |
|----------|----------|
| Строк | 289 |
| Размер | 13,582 байт |
| Функции | 7 |

**Функции верхнего уровня:**

- `cmd_start(message, state)` L19
- `process_first_name(message, state)` L53
- `process_last_name(message, state)` L93
- `process_function(message, state)` L128
- `process_category(message, state)` L156
- `process_cancel_payment_input(callback_query, state)` L233
- `process_back_to_main(callback_query, state)` L260

### Файл: `handlers/dashboard_handlers.py`

| Свойство | Значение |
|----------|----------|
| Строк | 270 |
| Размер | 14,092 байт |
| Функции | 5 |

**Функции верхнего уровня:**

- `show_admin_dashboard(callback_query)` L16
- `_format_dashboard_message(data)` L52
- `_create_dashboard_keyboard()` L151
- `show_detailed_stats(callback_query)` L179
- `_format_detailed_stats_message(data)` L213

### Файл: `handlers/user_handlers.py`

| Свойство | Значение |
|----------|----------|
| Строк | 1465 |
| Размер | 70,480 байт |
| Функции | 34 |

**Функции верхнего уровня:**

- `edit_profile_step(callback_query)` L33
- `process_edit_profile_first_name(message, state)` L54
- `process_edit_profile_last_name(message, state)` L84
- `process_edit_profile_function(message, state)` L113
- `process_edit_profile_category(message, state)` L134
- `cmd_link_email(message, state)` L179
- `link_email_step(callback_query, state)` L205
- `process_link_email_input(message, state)` L233
- `process_link_email_code(message, state)` L283
- `process_sign_up(callback_query)` L335
- `process_month(callback_query)` L359
- `process_tournament(callback_query)` L390
- `process_festmates_start(callback_query)` L488
- `process_festmates_month(callback_query)` L529
- `process_festmates_tournament(callback_query)` L578
- `process_cancel_registration(callback_query)` L656
- `process_cancel_reg_month(callback_query)` L686
- `process_cancel_reg_id(callback_query)` L720
- `process_confirm_cancel(callback_query)` L751
- `process_cancel_action(callback_query, state)` L819
- `my_registrations_step(callback_query)` L830
- `process_my_registrations_month(callback_query, state)` L854
- `main_reply_keyboard()` L900
- `handle_main_menu_button(message)` L908
- `setup_main_menu_button_handlers(dp)` L915
- `process_my_earnings(callback_query, state)` L919
- `process_earnings_detailed(callback_query, state)` L939
- `process_earnings_summary(callback_query, state)` L1006
- `process_payment_yes(callback_query, state)` L1056
- `process_payment_no(callback_query)` L1096

### Файл: `keyboards.py`

| Свойство | Значение |
|----------|----------|
| Строк | 171 |
| Размер | 8,572 байт |
| Функции | 12 |

**Функции верхнего уровня:**

- `main_menu()` L5
- `admin_menu_keyboard()` L22
- `cancel_keyboard(context_type)` L46
- `month_selection_keyboard(months, callback_prefix, back_callback)` L57
- `confirmation_keyboard(confirm_callback, cancel_callback)` L67
- `payment_reminder_keyboard(payment_id)` L78
- `earnings_menu_keyboard()` L89
- `admin_earnings_menu_keyboard()` L102
- `month_selection_earnings_keyboard(months)` L115
- `year_selection_earnings_keyboard(years)` L125
- `budget_reminder_keyboard(tournament_id)` L135
- `group_budget_reminder_keyboard(tournaments)` L147

### Файл: `main.py`

| Свойство | Значение |
|----------|----------|
| Строк | 454 |
| Размер | 24,714 байт |
| Функции | 8 |

**Функции верхнего уровня:**

- `reminder_job()` L105
- `payment_reminder_job()` L151
- `budget_reminder_job()` L175
- `on_startup(_)` L192
- `on_shutdown(_)` L224
- `_go_admin_menu(cb, state)` L328
- `_handle_callback_in_payment_state(cb, state)` L427
- `_debug_unhandled_cb(cb, state)` L440

### Файл: `manual_budget_test.py`

| Свойство | Значение |
|----------|----------|
| Строк | 321 |
| Размер | 13,144 байт |

### Файл: `manual_payment_input.py`

| Свойство | Значение |
|----------|----------|
| Строк | 243 |
| Размер | 9,742 байт |
| Функции | 5 |

**Функции верхнего уровня:**

- `list_unpaid_judges()` L24
- `list_judge_tournaments(user_id)` L66
- `input_payment(payment_id, amount)` L95
- `interactive_input()` L154
- `direct_input(payment_id, amount)` L222

### Файл: `manual_reminders.py`

| Свойство | Значение |
|----------|----------|
| Строк | 122 |
| Размер | 5,043 байт |
| Функции | 3 |

**Функции верхнего уровня:**

- `manual_budget_reminders()` L17
- `manual_payment_reminders()` L59
- `main()` L101

### Файл: `mass_update_payments.py`

| Свойство | Значение |
|----------|----------|
| Строк | 187 |
| Размер | 7,622 байт |
| Функции | 2 |

**Функции верхнего уровня:**

- `update_all_unpaid_payments(dry_run)` L25
- `main()` L156

### Файл: `migrate_to_new_season.py`

| Свойство | Значение |
|----------|----------|
| Строк | 142 |
| Размер | 5,391 байт |
| Функции | 6 |

**Функции верхнего уровня:**

- `backup_current_database()` L15
- `get_users_from_current_db()` L28
- `create_new_database()` L41
- `migrate_users(users, new_db_path)` L57
- `replace_database(new_db_path)` L91
- `main()` L102

### Файл: `models.py`

| Свойство | Значение |
|----------|----------|
| Строк | 156 |
| Размер | 8,168 байт |
| Классы | 7 |

**Классы:**

- `RegistrationStatus` (строка 9)
- `User` (строка 14)
- `Tournament` (строка 42)
- `Registration` (строка 60)
- `RegistrationCancellation` (строка 79)
- `JudgePayment` (строка 99)
  - Docstring: Таблица для отслеживания оплаты судей
- `TournamentBudget` (строка 132)
  - Docstring: Таблица для бюджетирования турниров

### Файл: `quick_budget_test.py`

| Свойство | Значение |
|----------|----------|
| Строк | 158 |
| Размер | 6,482 байт |
| Классы | 1 |
| Функции | 1 |

**Классы:**

- `QuickTestBot` (строка 13)
  - Docstring: Быстрый тестовый бот
  - `send_message(self, chat_id, text, reply_markup, parse_mode)` L16

**Функции верхнего уровня:**

- `main()` L29

### Файл: `repair_database.py`

| Свойство | Значение |
|----------|----------|
| Строк | 211 |
| Размер | 8,480 байт |
| Функции | 5 |

**Функции верхнего уровня:**

- `get_db_path()` L14
- `check_integrity(db_path)` L26
- `create_backup(db_path)` L51
- `repair_database(db_path)` L66
- `main()` L160

### Файл: `requirements.txt`

| Свойство | Значение |
|----------|----------|
| Строк | 13 |
| Размер | 234 байт |

### Файл: `reset_user_password.py`

| Свойство | Значение |
|----------|----------|
| Строк | 45 |
| Размер | 1,425 байт |
| Функции | 1 |

**Функции верхнего уровня:**

- `main()` L16

### Файл: `restore_database.py`

| Свойство | Значение |
|----------|----------|
| Строк | 71 |
| Размер | 2,862 байт |
| Функции | 1 |

**Функции верхнего уровня:**

- `main()` L19

### Файл: `restore_from_backup.py`

| Свойство | Значение |
|----------|----------|
| Строк | 106 |
| Размер | 3,988 байт |
| Функции | 3 |

**Функции верхнего уровня:**

- `list_backups()` L11
- `restore_backup(backup_file)` L36
- `main()` L61

### Файл: `safe_repair_database.py`

| Свойство | Значение |
|----------|----------|
| Строк | 224 |
| Размер | 8,739 байт |
| Функции | 6 |

**Функции верхнего уровня:**

- `get_db_path()` L15
- `create_backup(db_path)` L26
- `check_integrity(db_path)` L41
- `fix_wal_files(db_path)` L53
- `safe_repair_database(db_path)` L84
- `main()` L182

### Файл: `scripts/backfill_cancellations_from_bot_log.py`

| Свойство | Значение |
|----------|----------|
| Строк | 109 |
| Размер | 3,916 байт |
| Функции | 2 |

**Функции верхнего уровня:**

- `parse_cancellations()` L22
- `main()` L55

### Файл: `send_budget_reminders_manual.py`

| Свойство | Значение |
|----------|----------|
| Строк | 59 |
| Размер | 2,492 байт |
| Функции | 1 |

**Функции верхнего уровня:**

- `send_budget_reminders_manual()` L16

### Файл: `send_old_payment_reminders.py`

| Свойство | Значение |
|----------|----------|
| Строк | 61 |
| Размер | 2,558 байт |
| Функции | 1 |

**Функции верхнего уровня:**

- `send_old_payment_reminders()` L16

### Файл: `send_old_payment_reminders_fixed.py`

| Свойство | Значение |
|----------|----------|
| Строк | 67 |
| Размер | 2,731 байт |
| Функции | 1 |

**Функции верхнего уровня:**

- `send_old_payment_reminders()` L19

### Файл: `send_payment_reminders_manual.py`

| Свойство | Значение |
|----------|----------|
| Строк | 62 |
| Размер | 2,687 байт |
| Функции | 1 |

**Функции верхнего уровня:**

- `send_payment_reminders_manual()` L16

### Файл: `server_audit.py`

| Свойство | Значение |
|----------|----------|
| Строк | 1308 |
| Размер | 62,015 байт |
| Классы | 1 |
| Функции | 1 |

**Классы:**

- `ServerAuditor` (строка 16)
  - `__init__(self)` L17
  - `run_command(self, cmd, shell, capture_stderr)` L33
  - `get_system_info(self)` L57
  - `get_services(self)` L103
  - `get_ports(self)` L248
  - `get_processes(self)` L386
  - `scan_directory(self, path, max_depth, current_depth)` L551
  - `get_projects(self)` L632
  - `get_security_info(self)` L657
  - `get_network_info(self)` L722
  - `get_storage_info(self)` L749
  - `get_users_info(self)` L772
  - `get_disk_usage(self, min_size_mb)` L815
  - `get_cron_info(self)` L936
  - `generate_report(self, output_file)` L966

**Функции верхнего уровня:**

- `main()` L1248

### Файл: `services/budget_service.py`

| Свойство | Значение |
|----------|----------|
| Строк | 340 |
| Размер | 15,340 байт |
| Классы | 1 |
| Функции | 1 |

**Классы:**

- `BudgetService` (строка 18)
  - Docstring: Сервис для управления бюджетом турниров
  - `__init__(self, bot)` L21
  - `__del__(self)` L25
  - `send_budget_reminders(self)` L29
  - `_send_budget_reminder(self, tournament)` L79
  - `_send_group_budget_reminder(self, tournaments)` L102
  - `set_tournament_budget(self, tournament_id, total_budget)` L130
  - `_recalculate_admin_profit(self, tournament_id)` L170
  - `get_tournament_budget(self, tournament_id)` L199
  - `get_all_budgets(self)` L222
  - `get_admin_profit_summary(self)` L268
  - `update_judges_payment(self, tournament_id)` L319
  - `_get_current_season_start(self)` L323

**Функции верхнего уровня:**

- `get_budget_service(bot)` L334

### Файл: `services/dashboard_service.py`

| Свойство | Значение |
|----------|----------|
| Строк | 535 |
| Размер | 24,516 байт |
| Классы | 1 |
| Функции | 1 |

**Классы:**

- `DashboardService` (строка 24)
  - Docstring: Сервис для создания дашборда админа
  - `__init__(self)` L27
  - `__del__(self)` L30
  - `get_dashboard_data(self)` L34
  - `_get_judges_stats(self)` L55
  - `_get_tournaments_stats(self)` L97
  - `_get_registrations_stats(self)` L153
  - `_get_finances_stats(self)` L194
  - `_get_activity_stats(self)` L235
  - `_get_top_judges(self)` L272
  - `_get_recent_activity(self)` L300
  - `_get_season_info(self)` L337
  - `_get_alerts(self)` L361
  - `_get_current_season_start(self)` L408
  - `_get_current_season_end(self)` L416
  - `_get_budget_stats(self)` L424
  - `_get_refusals_stats(self)` L465

**Функции верхнего уровня:**

- `get_dashboard_service()` L529

### Файл: `services/excel_export.py`

| Свойство | Значение |
|----------|----------|
| Строк | 603 |
| Размер | 31,305 байт |
| Функции | 2 |

**Функции верхнего уровня:**

- `split_text(text, max_length)` L18
- `export_data(bot, callback_query, period, month, year)` L29

### Файл: `services/payment_system.py`

| Свойство | Значение |
|----------|----------|
| Строк | 670 |
| Размер | 33,243 байт |
| Классы | 1 |
| Функции | 1 |

**Классы:**

- `PaymentSystem` (строка 28)
  - Docstring: Класс для управления системой оплаты судей
  - `__init__(self, bot)` L31
  - `_msk_timezone()` L36
  - `_first_payment_reminder_at(self, tournament_date)` L39
  - `_as_msk(self, value)` L48
  - `_latest_payment_prompt_at(self, payment)` L54
  - `_last_payment_response_at(self, payment)` L66
  - `_has_unanswered_payment_prompt(self, payment)` L69
  - `_should_send_judge
---

## Статистика проекта

| Метрика | Значение |
|---------|----------|
| Файлов проанализировано | 105 |
| Директорий | 24 |
| HTTP маршрутов (оценка) | 35 |
| Python классов | 51 |
| Строк в reference | ~1,151,452 |
| Исходников включено полностью | 105 |

<p align="center"><i>Документация Ultra v2.0 · 2026-06-10</i></p>
