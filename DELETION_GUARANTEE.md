# Гарантии удаления турнира и связанных данных

## ✅ Текущая реализация

### 1. **Явное удаление в коде (основной метод)**

При удалении турнира через бота (`process_delete_confirm`) **явно удаляются** все связанные данные:

```python
# 1. Удаляем записи об оплате
payments_deleted = session.query(JudgePayment).filter(
    JudgePayment.tournament_id == tournament_id
).delete(synchronize_session=False)

# 2. Удаляем регистрации
registrations_deleted = session.query(Registration).filter(
    Registration.tournament_id == tournament_id
).delete(synchronize_session=False)

# 3. Удаляем бюджет турнира
budgets_deleted = session.query(TournamentBudget).filter(
    TournamentBudget.tournament_id == tournament_id
).delete(synchronize_session=False)

# 4. Удаляем сам турнир
session.delete(t)
session.commit()
```

**Гарантия:** ✅ Все данные удаляются явно в правильном порядке

### 2. **CASCADE на уровне БД (дополнительная защита)**

В моделях добавлены `ondelete='CASCADE'` для дополнительной защиты:

- ✅ `Registration.tournament_id` → `ondelete='CASCADE'`
- ✅ `JudgePayment.tournament_id` → `ondelete='CASCADE'`
- ✅ `TournamentBudget.tournament_id` → `ondelete='CASCADE'` (уже было)

**Гарантия:** ✅ Даже если код не удалит связанные данные, БД удалит их автоматически

### 3. **Relationship cascade (для Registration)**

В модели `Tournament` есть:
```python
registrations = relationship("Registration", back_populates="tournament", cascade="all, delete-orphan")
```

**Гарантия:** ✅ Registration удалятся автоматически через SQLAlchemy relationship

## 🛡️ Тройная защита

1. **Явное удаление в коде** - основной метод, работает всегда
2. **CASCADE на уровне БД** - защита на случай ошибок в коде
3. **Relationship cascade** - дополнительная защита для Registration

## 📊 Что удаляется при удалении турнира

| Таблица | Метод удаления | Гарантия |
|---------|---------------|----------|
| `judge_payments` | Явное удаление + CASCADE | ✅✅ |
| `registrations` | Явное удаление + CASCADE + Relationship | ✅✅✅ |
| `tournament_budgets` | Явное удаление + CASCADE | ✅✅ |
| `tournaments` | Прямое удаление | ✅ |

## ⚠️ Важно

**Для применения CASCADE на уровне БД нужно:**

1. Обновить модели (уже сделано)
2. Создать миграцию или пересоздать таблицы (если БД уже существует)

**Для существующей БД:**

Если БД уже существует, CASCADE может не работать сразу. Но **явное удаление в коде работает всегда**, так что это не критично.

Для применения CASCADE к существующей БД можно:

```sql
-- Для judge_payments
CREATE TABLE judge_payments_new (
    ...,
    tournament_id INTEGER REFERENCES tournaments(tournament_id) ON DELETE CASCADE
);
-- Скопировать данные и переименовать таблицы

-- Для registrations
CREATE TABLE registrations_new (
    ...,
    tournament_id INTEGER REFERENCES tournaments(tournament_id) ON DELETE CASCADE
);
-- Скопировать данные и переименовать таблицы
```

**Но это не обязательно**, так как явное удаление в коде уже работает.

## ✅ Вывод

**ДА, при удалении турнира через бота удалятся ВСЕ связанные записи:**

1. ✅ Регистрации (registrations)
2. ✅ Платежи (judge_payments)
3. ✅ Бюджеты (tournament_budgets)
4. ✅ Сам турнир (tournaments)

**Тройная защита гарантирует, что висячих записей не останется!**

## 🔧 Если что-то пошло не так

Если по какой-то причине остались висячие записи, используйте:

```bash
# Проверка висячих записей
python3 check_orphaned_data.py

# Принудительное удаление
python3 delete_tournament_force.py --name "Название" --date "DD.MM.YYYY"
```

Но с текущей реализацией это должно быть не нужно! 🎯


