'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import {
  Trophy,
  ClipboardList,
  Wallet,
  Calendar,
  Target,
  TrendingUp,
  Clock,
  CheckCircle,
  User,
  ChevronRight,
  Zap
} from 'lucide-react'
import { api } from '@/lib/api'

type UserInfo = {
  first_name?: string
  last_name?: string
  function?: string
}

type ProgressToNext = {
  current: number
  target: number
  next_label: string
}

type EarningsSummary = {
  total_amount?: number
  total_tournaments?: number
  average_amount?: number
  rating?: string
  progress_to_next?: ProgressToNext | null
}

type EarningsDetail = {
  monthly_earnings?: { month: string; total_amount: number; tournaments_count: number }[]
  tournament_earnings?: { name: string; date: string; amount: number }[]
}

type Registration = {
  registration_id: number
  status: string
  tournament: { name: string; date: string; month: string }
}

type Tournament = {
  tournament_id: number
  name: string
  date: string
  month: string
}

type Payment = {
  amount: number | null
  is_paid: boolean
}

function InstrumentPanel({
  title,
  value,
  sub,
  icon: Icon,
  href,
  accent = 'emerald',
  size = 'md'
}: {
  title: string
  value: string | number
  sub?: string
  icon: React.ElementType
  href?: string
  accent?: 'emerald' | 'cyan' | 'amber' | 'rose' | 'violet'
  size?: 'sm' | 'md' | 'lg'
}) {
  const accentColors = {
    emerald: 'border-emerald-200 bg-emerald-50 text-emerald-700',
    cyan: 'border-cyan-200 bg-cyan-50 text-cyan-700',
    amber: 'border-amber-200 bg-amber-50 text-amber-700',
    rose: 'border-rose-200 bg-rose-50 text-rose-700',
    violet: 'border-violet-200 bg-violet-50 text-violet-700'
  }
  const content = (
        <div
      className={`group relative overflow-hidden rounded-xl border-2 ${accentColors[accent]} p-4 transition-all hover:shadow-md`}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <Icon className="h-5 w-5 opacity-80" />
          <span className="text-xs font-medium uppercase tracking-wider opacity-70">{title}</span>
        </div>
        {href && (
          <ChevronRight className="h-4 w-4 opacity-50 transition group-hover:opacity-100" />
        )}
      </div>
      <div className={`mt-2 font-mono font-bold tabular-nums text-slate-800 ${size === 'lg' ? 'text-2xl md:text-3xl' : size === 'sm' ? 'text-lg' : 'text-xl md:text-2xl'}`}>
        {value}
      </div>
      {sub && <p className="mt-0.5 text-xs text-slate-500">{sub}</p>}
    </div>
  )
  return href ? (
    <Link href={href} className="block transition-transform hover:scale-[1.02] active:scale-[0.98]">
      {content}
    </Link>
  ) : (
    content
  )
}

function MiniBar({ value, max, label }: { value: number; max: number; label: string }) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-slate-600">
        <span>{label}</span>
        <span className="font-mono tabular-nums">{value} ₽</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-slate-200">
        <div
          className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-emerald-500 transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const [user, setUser] = useState<UserInfo | null>(null)
  const [earnings, setEarnings] = useState<EarningsSummary | null>(null)
  const [detail, setDetail] = useState<EarningsDetail | null>(null)
  const [payments, setPayments] = useState<Payment[]>([])
  const [regs, setRegs] = useState<Registration[]>([])
  const [tours, setTours] = useState<Tournament[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) return
    Promise.all([
      api<UserInfo>('/api/v1/users/me', { token }).catch(() => null),
      api<EarningsSummary>('/api/v1/earnings/my/summary', { token }).catch(() => null),
      api<EarningsDetail>('/api/v1/earnings/my/detail', { token }).catch(() => null),
      api<Payment[]>('/api/v1/earnings/my/payments?future_only=false', { token }).catch(() => []),
      api<Registration[]>('/api/v1/registrations/my?future_only=true', { token }).catch(() => []),
      api<Tournament[]>('/api/v1/tournaments?future_only=true', { token }).catch(() => [])
    ]).then(([u, e, d, p, r, t]) => {
      setUser(u ?? null)
      setEarnings(e ?? null)
      setDetail(d ?? null)
      setPayments(Array.isArray(p) ? p : [])
      setRegs(Array.isArray(r) ? r : [])
      setTours(Array.isArray(t) ? t : [])
    }).finally(() => setLoading(false))
  }, [])

  const pendingCount = regs.filter((r) => r.status === 'pending').length
  const approvedCount = regs.filter((r) => r.status === 'approved').length
  const paidCount = payments.filter((p) => p.is_paid).length
  const unpaidCount = payments.filter((p) => !p.is_paid).length
  const totalPaid = payments.filter((p) => p.is_paid).reduce((s, p) => s + (p.amount ?? 0), 0)
  const totalUnpaid = payments.filter((p) => !p.is_paid).reduce((s, p) => s + (p.amount ?? 0), 0)
  const monthly = detail?.monthly_earnings ?? []
  const maxMonthly = Math.max(...monthly.map((m) => m.total_amount), 1)
  const nextTournament = regs.find((r) => r.status === 'approved') ?? regs[0]

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-800 md:text-3xl">
            Панель управления
          </h1>
          <p className="mt-1 text-slate-600">
            Привет, {user?.first_name ?? 'Судья'}! Вот твоя статистика.
          </p>
        </div>
        {earnings?.rating && (
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-4">
            <div className="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2">
              <Zap className="h-5 w-5 text-amber-600" />
              <span className="font-semibold text-amber-800">{earnings.rating}</span>
            </div>
            {earnings.progress_to_next && (
              <div className="flex min-w-[200px] flex-col gap-1 rounded-lg border border-slate-200 bg-slate-50 px-4 py-2">
                <span className="text-xs font-medium text-slate-600">
                  До {earnings.progress_to_next.next_label}: {earnings.progress_to_next.current}/{earnings.progress_to_next.target} турниров
                </span>
                <div className="h-2 overflow-hidden rounded-full bg-slate-200">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-amber-400 to-amber-600 transition-all"
                    style={{ width: `${Math.min(100, (earnings.progress_to_next.current / earnings.progress_to_next.target) * 100)}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Main gauges */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <InstrumentPanel
          title="Всего выплат"
          value={earnings?.total_amount != null ? `${earnings.total_amount.toLocaleString('ru-RU')} ₽` : '—'}
          sub={earnings?.total_tournaments != null ? `за ${earnings.total_tournaments} турниров` : undefined}
          icon={Wallet}
          href="/dashboard/earnings"
          accent="emerald"
          size="lg"
        />
        <InstrumentPanel
          title="Турниров впереди"
          value={tours.length}
          sub="предстоящих"
          icon={Trophy}
          href="/dashboard/tournaments"
          accent="cyan"
          size="lg"
        />
        <InstrumentPanel
          title="Мои заявки"
          value={regs.length}
          sub={`✓ ${approvedCount} одобрено · ⏳ ${pendingCount} на рассмотрении`}
          icon={ClipboardList}
          href="/dashboard/registrations"
          accent="amber"
          size="md"
        />
        <InstrumentPanel
          title="Средний чек"
          value={earnings?.average_amount != null ? `${Math.round(earnings.average_amount).toLocaleString('ru-RU')} ₽` : '—'}
          sub="за турнир"
          icon={TrendingUp}
          accent="violet"
          size="md"
        />
      </div>

      {/* Achievements / Progress */}
      {(earnings?.rating || earnings?.progress_to_next) && (
        <div className="rounded-xl border border-amber-200 bg-amber-50/30 p-5 shadow-sm">
          <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-amber-800">
            <Trophy className="h-4 w-4" />
            Достижения
          </h2>
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-3">
              <span className="text-2xl font-bold text-amber-800">{earnings?.rating ?? '—'}</span>
              <span className="text-sm text-slate-600">
                {earnings?.total_tournaments ?? 0} оплаченных турниров
              </span>
            </div>
            {earnings?.progress_to_next && (
              <div className="min-w-[240px]">
                <p className="mb-1 text-xs font-medium text-slate-600">
                  Прогресс до {earnings.progress_to_next.next_label}
                </p>
                <div className="flex items-center gap-2">
                  <div className="h-3 flex-1 overflow-hidden rounded-full bg-slate-200">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-amber-400 to-amber-600"
                      style={{ width: `${Math.min(100, (earnings.progress_to_next.current / earnings.progress_to_next.target) * 100)}%` }}
                    />
                  </div>
                  <span className="text-sm font-mono font-medium text-slate-700">
                    {earnings.progress_to_next.current}/{earnings.progress_to_next.target}
                  </span>
                </div>
              </div>
            )}
            {!earnings?.progress_to_next && earnings?.rating && (
              <p className="text-sm font-medium text-amber-700">Максимальный статус достигнут</p>
            )}
          </div>
        </div>
      )}

      {/* Second row: payments breakdown + next tournament */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Payments status */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-slate-600">
            <Target className="h-4 w-4" />
            Статус выплат
          </h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4">
              <div className="flex items-center gap-2 text-emerald-700">
                <CheckCircle className="h-4 w-4" />
                <span className="text-xs font-medium uppercase">Оплачено</span>
              </div>
              <p className="mt-1 font-mono text-xl font-bold text-slate-800">
                {paidCount} шт · {totalPaid.toLocaleString('ru-RU')} ₽
              </p>
            </div>
            <Link
              href="/dashboard/earnings"
              className="rounded-lg border border-amber-200 bg-amber-50 p-4 transition hover:border-amber-300 hover:bg-amber-100"
            >
              <div className="flex items-center gap-2 text-amber-700">
                <Clock className="h-4 w-4" />
                <span className="text-xs font-medium uppercase">Ожидают</span>
              </div>
              <p className="mt-1 font-mono text-xl font-bold text-slate-800">
                {unpaidCount} шт · {totalUnpaid.toLocaleString('ru-RU')} ₽
              </p>
              <p className="mt-1 text-xs text-amber-600">Нажмите, чтобы посмотреть</p>
            </Link>
          </div>
          <Link
            href="/dashboard/earnings"
            className="mt-4 flex items-center justify-center gap-2 rounded-lg border border-slate-200 py-2.5 text-sm text-slate-600 transition hover:border-slate-300 hover:bg-slate-50"
          >
            Подробнее о выплатах
            <ChevronRight className="h-4 w-4" />
          </Link>
        </div>

        {/* Next tournament */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-slate-600">
            <Calendar className="h-4 w-4" />
            Ближайший турнир
          </h2>
          {nextTournament ? (
            <div className="rounded-lg border border-cyan-200 bg-cyan-50 p-4">
              <p className="font-mono text-lg font-bold text-slate-800">
                {nextTournament.tournament?.name ?? 'Турнир'}
              </p>
              <p className="mt-1 text-sm text-slate-600">
                {nextTournament.tournament?.date} · {nextTournament.tournament?.month}
              </p>
              <span
                className={`mt-2 inline-block rounded px-2 py-0.5 text-xs font-medium ${
                  nextTournament.status === 'approved'
                    ? 'bg-emerald-100 text-emerald-800'
                    : nextTournament.status === 'pending'
                      ? 'bg-amber-100 text-amber-800'
                      : 'bg-slate-200 text-slate-600'
                }`}
              >
                {nextTournament.status === 'approved' ? 'Одобрено' : nextTournament.status === 'pending' ? 'На рассмотрении' : 'Отклонено'}
              </span>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-slate-300 py-8 text-slate-500">
              <Calendar className="mb-2 h-10 w-10 opacity-50" />
              <p>Нет предстоящих заявок</p>
              <Link
                href="/dashboard/tournaments"
                className="mt-2 text-sm text-cyan-600 hover:underline"
              >
                Выбрать турнир →
              </Link>
            </div>
          )}
          <Link
            href="/dashboard/registrations"
            className="mt-4 flex items-center justify-center gap-2 rounded-lg border border-slate-200 py-2.5 text-sm text-slate-600 transition hover:border-slate-300 hover:bg-slate-50"
          >
            Все заявки
            <ChevronRight className="h-4 w-4" />
          </Link>
        </div>
      </div>

      {/* Monthly earnings chart */}
      {monthly.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-slate-600">
            <TrendingUp className="h-4 w-4" />
            Выплаты по месяцам
          </h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {monthly.slice(0, 8).map((m) => (
              <MiniBar
                key={m.month}
                value={m.total_amount}
                max={maxMonthly}
                label={m.month}
              />
            ))}
          </div>
          <Link
            href="/dashboard/earnings"
            className="mt-4 flex items-center justify-center gap-2 rounded-lg border border-slate-200 py-2.5 text-sm text-slate-600 transition hover:border-slate-300 hover:bg-slate-50"
          >
            Полная статистика
            <ChevronRight className="h-4 w-4" />
          </Link>
        </div>
      )}

      {/* Quick links */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Link
          href="/dashboard/tournaments"
          className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm transition hover:border-cyan-300 hover:bg-cyan-50/50"
        >
          <Trophy className="h-5 w-5 text-cyan-600" />
          <span className="text-sm font-medium text-slate-700">Турниры</span>
        </Link>
        <Link
          href="/dashboard/registrations"
          className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm transition hover:border-amber-300 hover:bg-amber-50/50"
        >
          <ClipboardList className="h-5 w-5 text-amber-600" />
          <span className="text-sm font-medium text-slate-700">Заявки</span>
        </Link>
        <Link
          href="/dashboard/earnings"
          className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm transition hover:border-emerald-300 hover:bg-emerald-50/50"
        >
          <Wallet className="h-5 w-5 text-emerald-600" />
          <span className="text-sm font-medium text-slate-700">Выплаты</span>
        </Link>
        <Link
          href="/dashboard/profile"
          className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm transition hover:border-violet-300 hover:bg-violet-50/50"
        >
          <User className="h-5 w-5 text-violet-600" />
          <span className="text-sm font-medium text-slate-700">Профиль</span>
        </Link>
      </div>
    </div>
  )
}
