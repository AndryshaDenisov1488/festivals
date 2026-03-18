from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Index, Float, DateTime, Boolean, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import date, datetime, timezone

Base = declarative_base()

# Возможные статусы заявки
class RegistrationStatus:
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'

class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    function = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)

    # Новые поля для веб-версии
    email = Column(String(255), nullable=True, unique=True, index=True)
    email_verified = Column(Boolean, nullable=False, default=False)
    is_blocked = Column(Boolean, nullable=False, default=False)
    is_admin = Column(Boolean, nullable=False, default=False)
    email_verification_code = Column(String(20), nullable=True)
    email_verification_expires_at = Column(DateTime, nullable=True)
    password_hash = Column(String(255), nullable=True)

    registrations = relationship("Registration", back_populates="user", cascade="all, delete-orphan")
    
    # Ограничения для валидации данных
    __table_args__ = (
        CheckConstraint('length(first_name) >= 2', name='check_first_name_length'),
        CheckConstraint('length(last_name) >= 2', name='check_last_name_length'),
        CheckConstraint('length(function) >= 2', name='check_function_length'),
        CheckConstraint('length(category) >= 1', name='check_category_length'),
    )

class Tournament(Base):
    __tablename__ = 'tournaments'

    tournament_id = Column(Integer, primary_key=True, index=True)
    month = Column(String(20), nullable=False)  # Название месяца (например, "Январь", "Февраль" и т.д.)
    date = Column(Date, nullable=False)     # Дата турнира
    name = Column(String(200), nullable=False)   # Название турнира
    #location = Column(String, nullable=False)
    #time = Column(String, nullable=True)

    registrations = relationship("Registration", back_populates="tournament", cascade="all, delete-orphan")
    
    # Ограничения для валидации данных
    __table_args__ = (
        CheckConstraint('length(month) >= 3', name='check_month_length'),
        CheckConstraint('length(name) >= 3', name='check_tournament_name_length'),
    )

class Registration(Base):
    __tablename__ = 'registrations'

    registration_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    tournament_id = Column(Integer, ForeignKey('tournaments.tournament_id', ondelete='CASCADE'), nullable=False)
    status = Column(String, default=RegistrationStatus.PENDING, nullable=False)

    user = relationship("User", back_populates="registrations")
    tournament = relationship("Tournament", back_populates="registrations")
    
    # Индексы для улучшения производительности
    __table_args__ = (
        Index('idx_user_tournament', 'user_id', 'tournament_id'),
        Index('idx_tournament_status', 'tournament_id', 'status'),
        Index('idx_user_status', 'user_id', 'status'),
    )

class JudgePayment(Base):
    """Таблица для отслеживания оплаты судей"""
    __tablename__ = 'judge_payments'
    
    payment_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    tournament_id = Column(Integer, ForeignKey('tournaments.tournament_id', ondelete='CASCADE'), nullable=False)
    amount = Column(Float, nullable=True)  # Сумма оплаты (может быть None если не оплачено)
    is_paid = Column(Boolean, default=False, nullable=False)  # Оплачено ли
    payment_date = Column(DateTime, nullable=True)  # Дата оплаты
    reminder_sent = Column(Boolean, default=False, nullable=False)  # Отправлено ли напоминание
    reminder_date = Column(DateTime, nullable=True)  # Дата отправки напоминания
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    user = relationship("User")
    tournament = relationship("Tournament")
    
    # Индексы для улучшения производительности
    __table_args__ = (
        Index('idx_user_payment', 'user_id'),
        Index('idx_tournament_payment', 'tournament_id'),
        Index('idx_payment_status', 'is_paid'),
        Index('idx_reminder_status', 'reminder_sent'),
        # Ограничения для валидации данных
        CheckConstraint('amount IS NULL OR amount >= 0', name='check_amount_positive'),
    )


class TournamentBudget(Base):
    """Таблица для бюджетирования турниров"""
    __tablename__ = 'tournament_budgets'

    budget_id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey('tournaments.tournament_id', ondelete='CASCADE'), nullable=False, unique=True)
    total_budget = Column(Float, nullable=False)  # Общий бюджет турнира
    judges_payment = Column(Float, nullable=True)  # Выплачено судьям
    admin_profit = Column(Float, nullable=True)  # Прибыль админа (остаток)
    budget_set_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)  # Дата установки бюджета
    reminder_sent = Column(Boolean, default=False, nullable=False)  # Отправлено ли напоминание
    reminder_date = Column(DateTime, nullable=True)  # Дата отправки напоминания

    tournament = relationship("Tournament")

    # Индексы для улучшения производительности
    __table_args__ = (
        Index('idx_tournament_budget', 'tournament_id'),
        Index('idx_budget_reminder', 'reminder_sent'),
        # Ограничения для валидации данных
        CheckConstraint('total_budget > 0', name='check_total_budget_positive'),
        CheckConstraint('judges_payment IS NULL OR judges_payment >= 0', name='check_judges_payment_positive'),
        CheckConstraint('admin_profit IS NULL OR admin_profit >= 0', name='check_admin_profit_positive'),
    )
