---
name: judges-bot-v2
description: >-
  ULTRA-документация Judges Bot v2 (festsfs.ru). Путь: /root/judges_bot_v2.
  reference.md содержит ПОЛНЫЙ исходный код всех файлов, API, модели, схемы БД.
  При ЛЮБОЙ задаче — читать reference.md ПЕРВЫМ. Не сканировать проект. Сервер: ffkm-server.
---

# Judges Bot v2 — Ultra Skill

## ОБЯЗАТЕЛЬНО ПЕРВЫМ ДЕЛОМ

1. **[reference.md](reference.md)** — исчерпывающая документация (до 3.5MB):
   - Часть I: Executive Summary
   - Часть IV: Все API маршруты
   - Часть V: Все классы и модели
   - Часть VII: Схема БД
   - Часть XII: Пофайловый анализ (каждый файл)
   - **Часть XIII: ПОЛНЫЙ исходный код всех файлов**
2. **[README.md](../../README.md)** — обзор для человека
3. Сервер: `/root/.cursor/skills/ffkm-server/SKILL.md`

## Карточка

| | |
|--|--|
| Путь | `/root/judges_bot_v2` |
| URL | https://festsfs.ru |
| Порт | 3000 (Next.js), 8101 (API) |
| БД | SQLite: bot_database.db |
| Systemd | `judges-bot, judges-api, judges-web` |

## Команды

```bash
systemctl restart judges-bot judges-api judges-web
journalctl -u judges-bot -f
```

## Навигация по reference.md

| Часть | Содержание |
|-------|------------|
| I | Резюме, статистика, архитектура |
| II | Зависимости Python/JS |
| III | Каталог всех файлов |
| IV | API маршруты (полный реестр) |
| V | Классы и модели |
| VI | Переменные окружения |
| VII | Схема БД |
| VIII–IX | Systemd, Nginx |
| X | Git |
| XI | Операции, деплой |
| XII | Пофайловый анализ |
| **XIII** | **Полный исходный код** |
| XIV | README, ТЗ, приложения |
