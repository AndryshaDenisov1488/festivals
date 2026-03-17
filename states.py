from aiogram.dispatcher.filters.state import State, StatesGroup

# Состояния для регистрации судьи
class RegisterReferee(StatesGroup):
    waiting_for_first_name = State()
    waiting_for_last_name = State()
    waiting_for_function = State()
    waiting_for_category = State()

# Состояния для добавления турнира
class AddTournament(StatesGroup):
    waiting_for_month = State()
    waiting_for_date = State()
    waiting_for_name = State()

# Состояния для редактирования профиля
class EditProfile(StatesGroup):
    waiting_for_first_name = State()
    waiting_for_last_name = State()
    waiting_for_function = State()
    waiting_for_category = State()

# Состояния для массовой рассылки
class SendAllMessages(StatesGroup):
    waiting_for_message = State()

# Состояния для редактирования турнира
class EditTournament(StatesGroup):
    waiting_for_month = State()
    waiting_for_tournament_selection = State()
    waiting_for_new_date = State()
    waiting_for_new_name = State()

# Состояния для удаления турнира
class DeleteTournament(StatesGroup):
    waiting_for_month = State()               # выбор месяца
    waiting_for_tournament_selection = State()# выбор турнира
    waiting_for_confirmation = State()        # подтверждение удаления

# Состояния для просмотра "Мои записи"
class MyRegistrations(StatesGroup):
    waiting_for_month = State()

# Состояния для проверки записей (админ)
class CheckRegistrations(StatesGroup):
    waiting_for_month = State()

# Состояния для системы оплаты
class PaymentAmount(StatesGroup):
    waiting_for_amount = State()

# Состояния для исправления заработка судьей
class CorrectEarnings(StatesGroup):
    waiting_for_tournament_selection = State()
    waiting_for_amount = State()

# Состояния для системы бюджетирования
class BudgetInput(StatesGroup):
    waiting_for_amount = State()

# Состояния для ручного ввода заработка админом
class ManualPaymentInput(StatesGroup):
    waiting_for_judge_selection = State()
    waiting_for_tournament_selection = State()
    waiting_for_amount = State()

# Состояния для привязки email (вход на веб-портал)
class LinkEmail(StatesGroup):
    waiting_for_email = State()
    waiting_for_code = State()