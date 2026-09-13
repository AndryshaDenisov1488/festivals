'use client'

import { useEffect, useMemo, useState } from 'react'
import { api } from '@/lib/api'
import { Send, DollarSign, FileSpreadsheet, ClipboardList, Check, X, Users, Trophy, PlusCircle, Pencil, Trash2, ChevronDown, ChevronRight, Wallet, Mail } from 'lucide-react'
import MonthFilter, { type MonthFilterValue } from '@/components/MonthFilter'
import SeasonFilter from '@/components/SeasonFilter'

type Budget = {
  tournament_id: number
  tournament_name: string
  tournament_date: string
  total_budget: number
  judges_payment: number
  admin_profit: number
  budget_set?: boolean
}

type AdminRegistration = {
  registration_id: number
  tournament_id: number
  tournament_name: string
  tournament_date: string
  tournament_month: string
  user_id: number
  user_name: string
  status: string
}

type AdminUser = {
  user_id: number
  first_name: string
  last_name: string
  function: string
  category: string
  email: string | null
  is_blocked: boolean
  regs_approved?: number
  regs_pending?: number
  regs_rejected?: number
  regs_total?: number
  approved_pct?: number
  rejected_pct?: number
  season_refusals?: number
  season_approved_assignments?: number
  season_refusal_pct?: number
}

type AdminTournament = {
  tournament_id: number
  name: string
  date: string
  month: string
}

type RefusalsMonthlyStat = {
  month_key: string
  month: string
  refusals: number
}

type RefusalsSeasonStat = {
  key?: string
  label?: string
  start: string
  end: string
  refusals: number
  approved_assignments: number
  refusal_pct: number
  responsibility_score: number
  responsibility_label: string
}

type SeasonOption = {
  key: string
  label: string
  start?: string | null
  end?: string | null
  is_current?: boolean
}

type RefusalsJudgeStat = {
  user_id: number
  user_name: string
  refusals: number
  approved_assignments: number
  refusal_pct: number
}

type RefusalsStatsResponse = {
  season: RefusalsSeasonStat
  monthly: RefusalsMonthlyStat[]
  by_judge?: RefusalsJudgeStat[]
}

export default function AdminPage() {
  const [broadcastMsg, setBroadcastMsg] = useState('')
  const [broadcastLoading, setBroadcastLoading] = useState(false)
  const [broadcastResult, setBroadcastResult] = useState<{ total?: number; ok?: number; fail?: number } | null>(null)

  const [budgets, setBudgets] = useState<Budget[]>([])
  const [budgetSummary, setBudgetSummary] = useState<{
    total_profit?: number
    monthly_profit?: number
    seasonal_profit?: number
    tournaments_count?: number
  } | null>(null)
  const [editingBudget, setEditingBudget] = useState<{ id: number; value: string } | null>(null)
  const [budgetsLoading, setBudgetsLoading] = useState(false)

  const [registrations, setRegistrations] = useState<AdminRegistration[]>([])
  const [regsLoading, setRegsLoading] = useState(false)
  const [refusalsStats, setRefusalsStats] = useState<RefusalsStatsResponse | null>(null)
  const [regsFilter, setRegsFilter] = useState<'pending' | 'approved' | 'rejected' | ''>('pending')
  const [regsMonthFilter, setRegsMonthFilter] = useState<MonthFilterValue>('future')
  const [regsSearch, setRegsSearch] = useState('')
  const [expandedTournamentIds, setExpandedTournamentIds] = useState<Set<number>>(new Set())
  const [budgetsMonthFilter, setBudgetsMonthFilter] = useState<MonthFilterValue>('all')

  const [exportMonth, setExportMonth] = useState('')
  const [exportYear, setExportYear] = useState('')
  const [exportSeason, setExportSeason] = useState('')
  const [exportLoading, setExportLoading] = useState(false)
  const [seasonOptions, setSeasonOptions] = useState<SeasonOption[]>([])
  const [statsSeason, setStatsSeason] = useState('')

  type JudgeEarnings = {
    user_id: number
    user_name: string
    email: string
    function?: string
    category?: string
    total_tournaments: number
    with_amount: number
    without_amount: number
    total_amount: number
    tournaments: Array<{
      payment_id: number
      tournament_name: string
      tournament_date: string
      tournament_month: string
      amount: number | null
      is_paid: boolean
    }>
    without_amount_list: Array<{
      payment_id: number
      tournament_name: string
      tournament_date: string
    }>
  }
  const [earnings, setEarnings] = useState<JudgeEarnings[]>([])
  const [earningsLoading, setEarningsLoading] = useState(false)
  const [earningsSearch, setEarningsSearch] = useState('')
  const [expandedEarningsIds, setExpandedEarningsIds] = useState<Set<number>>(new Set())
  const [expandedEarningsSumIds, setExpandedEarningsSumIds] = useState<Set<number>>(new Set())
  const [earningsRequestLoading, setEarningsRequestLoading] = useState<number | null>(null)
  const [editingPaymentId, setEditingPaymentId] = useState<number | null>(null)
  const [editingPaymentValue, setEditingPaymentValue] = useState('')
  const [savingPaymentId, setSavingPaymentId] = useState<number | null>(null)

  const [resultToast, setResultToast] = useState<{
    type: 'approved' | 'rejected'
    userName: string
    tournamentName: string
  } | null>(null)

  const [users, setUsers] = useState<AdminUser[]>([])
  const [usersSearch, setUsersSearch] = useState('')
  const [usersLoading, setUsersLoading] = useState(false)
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null)
  const [userForm, setUserForm] = useState({ first_name: '', last_name: '', function: '', category: '', is_blocked: false })

  const [tournaments, setTournaments] = useState<AdminTournament[]>([])
  const [tournamentsMonthFilter, setTournamentsMonthFilter] = useState<MonthFilterValue>('all')
  const [tournamentsSearch, setTournamentsSearch] = useState('')
  const [tournamentsLoading, setTournamentsLoading] = useState(false)
  const [showCreateTournament, setShowCreateTournament] = useState(false)
  const [createTournamentLoading, setCreateTournamentLoading] = useState(false)
  const [successToast, setSuccessToast] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'registrations' | 'tournaments' | 'users' | 'budgets' | 'earnings' | 'broadcast' | 'export'>('registrations')
  const [editingTournament, setEditingTournament] = useState<AdminTournament | null>(null)
  const [tournamentForm, setTournamentForm] = useState({ name: '', date: '', month: '' })

  const showSuccess = (msg: string) => {
    setSuccessToast(msg)
    setTimeout(() => setSuccessToast(null), 3000)
  }

  const MONTH_NAMES = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

  const getMonthFromDate = (dateStr: string) => {
    if (!dateStr) return MONTH_NAMES[new Date().getMonth()]
    const d = new Date(dateStr + 'T12:00:00')
    if (isNaN(d.getTime())) return MONTH_NAMES[new Date().getMonth()]
    return MONTH_NAMES[d.getMonth()]
  }

  const getDefaultMonth = () => MONTH_NAMES[new Date().getMonth()]

  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null

  const loadBudgets = () => {
    if (!token) return
    setBudgetsLoading(true)
    const params = new URLSearchParams()
    if (budgetsMonthFilter === 'future') params.set('future_only', 'true')
    else if (budgetsMonthFilter === 'all') params.set('future_only', 'false')
    else params.set('month', budgetsMonthFilter)
    Promise.all([
      api<Budget[]>(`/api/v1/admin/budgets?${params}`, { token }),
      api<{ total_profit?: number; monthly_profit?: number; seasonal_profit?: number; tournaments_count?: number }>('/api/v1/admin/budgets/summary', { token })
    ])
      .then(([b, s]) => {
        setBudgets(b ?? [])
        setBudgetSummary(s ?? null)
      })
      .catch(() => setBudgets([]))
      .finally(() => setBudgetsLoading(false))
  }

  const loadRegistrations = () => {
    if (!token) return
    setRegsLoading(true)
    const params = new URLSearchParams()
    if (regsFilter && regsFilter !== 'pending') params.set('status', regsFilter)
    if (regsMonthFilter === 'future') params.set('future_only', 'true')
    else if (regsMonthFilter === 'all') params.set('future_only', 'false')
    else params.set('month', regsMonthFilter)
    if (regsSearch.trim()) params.set('search', regsSearch.trim())
    if (statsSeason) params.set('season', statsSeason)
    api<AdminRegistration[]>(`/api/v1/admin/registrations?${params}`, { token })
      .then(setRegistrations)
      .catch(() => setRegistrations([]))
      .finally(() => setRegsLoading(false))

    api<RefusalsStatsResponse>(`/api/v1/admin/registrations/refusals-stats?season=${encodeURIComponent(statsSeason)}`, { token })
      .then(setRefusalsStats)
      .catch(() => setRefusalsStats(null))
  }

  const loadSeasons = () => {
    if (!token) return
    api<SeasonOption[]>('/api/v1/admin/seasons', { token })
      .then((items) => {
        if (items?.length) {
          setSeasonOptions(items)
          const current = items.find((s) => s.is_current)
          if (current) {
            setStatsSeason((prev) => prev || current.key)
            setExportSeason((prev) => prev || current.key)
          }
        }
      })
      .catch(() => {})
  }

  const loadUsers = () => {
    if (!token) return
    setUsersLoading(true)
    const params = new URLSearchParams()
    if (usersSearch.trim()) params.set('search', usersSearch.trim())
    params.set('season', statsSeason)
    api<AdminUser[]>(`/api/v1/admin/users?${params}`, { token })
      .then(setUsers)
      .catch(() => setUsers([]))
      .finally(() => setUsersLoading(false))
  }

  const loadEarnings = () => {
    if (!token) return
    setEarningsLoading(true)
    const params = new URLSearchParams()
    if (earningsSearch.trim()) params.set('search', earningsSearch.trim())
    api<JudgeEarnings[]>(`/api/v1/admin/earnings?${params}`, { token })
      .then(setEarnings)
      .catch(() => setEarnings([]))
      .finally(() => setEarningsLoading(false))
  }

  const loadTournaments = () => {
    if (!token) return
    setTournamentsLoading(true)
    const params = new URLSearchParams()
    if (tournamentsMonthFilter === 'future') params.set('future_only', 'true')
    else if (tournamentsMonthFilter !== 'all') params.set('month', tournamentsMonthFilter)
    if (tournamentsSearch.trim()) params.set('search', tournamentsSearch.trim())
    api<AdminTournament[]>(`/api/v1/admin/tournaments?${params}`, { token })
      .then(setTournaments)
      .catch(() => setTournaments([]))
      .finally(() => setTournamentsLoading(false))
  }

  useEffect(() => {
    loadBudgets()
  }, [token, budgetsMonthFilter])

  useEffect(() => {
    loadSeasons()
  }, [token])

  useEffect(() => {
    const id = setTimeout(loadRegistrations, regsSearch ? 200 : 0)
    return () => clearTimeout(id)
  }, [token, regsFilter, regsMonthFilter, regsSearch, statsSeason])

  useEffect(() => {
    const id = setTimeout(loadUsers, usersSearch ? 200 : 0)
    return () => clearTimeout(id)
  }, [token, usersSearch, statsSeason])

  useEffect(() => {
    const id = setTimeout(loadTournaments, tournamentsSearch ? 200 : 0)
    return () => clearTimeout(id)
  }, [token, tournamentsMonthFilter, tournamentsSearch])

  useEffect(() => {
    if (activeTab === 'earnings' && token) {
      const id = setTimeout(loadEarnings, earningsSearch ? 200 : 0)
      return () => clearTimeout(id)
    }
  }, [token, earningsSearch, activeTab])

  const handleBroadcast = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!broadcastMsg.trim() || !token) return
    setBroadcastLoading(true)
    setBroadcastResult(null)
    try {
      const res = await api<{ total: number; ok: number; fail: number }>(
        '/api/v1/admin/broadcast',
        { method: 'POST', body: JSON.stringify({ message: broadcastMsg.trim() }), token }
      )
      setBroadcastResult(res)
    } catch {
      setBroadcastResult({ total: 0, ok: 0, fail: 0 })
    } finally {
      setBroadcastLoading(false)
    }
  }

  const handleSetBudget = async (tournamentId: number, value: string) => {
    const num = parseFloat(value.replace(',', '.'))
    if (isNaN(num) || num <= 0 || !token) return
    try {
      await api(`/api/v1/admin/budgets/${tournamentId}`, {
        method: 'POST',
        body: JSON.stringify({ total_budget: num }),
        token
      })
      setEditingBudget(null)
      loadBudgets()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Ошибка')
    }
  }

  const regsByTournament = useMemo(() => {
    const map = new Map<number, { tournament_name: string; tournament_date: string; tournament_month: string; regs: AdminRegistration[] }>()
    for (const r of registrations) {
      const existing = map.get(r.tournament_id)
      if (existing) {
        existing.regs.push(r)
      } else {
        map.set(r.tournament_id, {
          tournament_name: r.tournament_name,
          tournament_date: r.tournament_date,
          tournament_month: r.tournament_month,
          regs: [r]
        })
      }
    }
    return Array.from(map.entries()).map(([tournament_id, data]) => ({ tournament_id, ...data }))
  }, [registrations])

  const toggleTournamentExpand = (id: number) => {
    setExpandedTournamentIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const handleApprove = async (r: AdminRegistration) => {
    if (!token) return
    try {
      await api(`/api/v1/admin/registrations/${r.registration_id}/approve`, { method: 'POST', token })
      setResultToast({ type: 'approved', userName: r.user_name, tournamentName: r.tournament_name })
      setRegistrations((prev) =>
        prev.map((x) => (x.registration_id === r.registration_id ? { ...x, status: 'approved' as const } : x))
      )
      setTimeout(() => setResultToast(null), 2500)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Ошибка')
    }
  }

  const handleReject = async (r: AdminRegistration) => {
    if (!token) return
    try {
      await api(`/api/v1/admin/registrations/${r.registration_id}/reject`, { method: 'POST', token })
      setResultToast({ type: 'rejected', userName: r.user_name, tournamentName: r.tournament_name })
      setRegistrations((prev) =>
        prev.map((x) => (x.registration_id === r.registration_id ? { ...x, status: 'rejected' as const } : x))
      )
      setTimeout(() => setResultToast(null), 2500)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Ошибка')
    }
  }

  const selectedSeasonLabel = seasonOptions.find((s) => s.key === statsSeason)?.label ?? statsSeason

  const downloadExport = async (url: string, filename: string, successMessage: string) => {
    if (!token) return
    setExportLoading(true)
    try {
      const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      if (!res.ok) {
        const detail = await res.text()
        throw new Error(detail || 'Ошибка экспорта')
      }
      const blob = await res.blob()
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = filename
      a.click()
      URL.revokeObjectURL(a.href)
      showSuccess(successMessage)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Ошибка')
    } finally {
      setExportLoading(false)
    }
  }

  const handleExportMonth = async () => {
    if (!exportMonth || !token) return
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8100'
    await downloadExport(
      `${apiUrl}/api/v1/admin/exports/month?month=${encodeURIComponent(exportMonth)}`,
      `export_${exportMonth}.xlsx`,
      'Экспорт за месяц скачан'
    )
  }

  const handleSaveUser = async () => {
    if (!token || !editingUser) return
    try {
      await api(`/api/v1/admin/users/${editingUser.user_id}`, {
        method: 'PATCH',
        body: JSON.stringify({
          first_name: userForm.first_name,
          last_name: userForm.last_name,
          function: userForm.function,
          category: userForm.category,
          is_blocked: userForm.is_blocked
        }),
        token
      })
      setEditingUser(null)
      loadUsers()
      showSuccess('Пользователь обновлён')
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Ошибка')
    }
  }

  const handleCreateTournament = async () => {
    if (!token || !tournamentForm.name || !tournamentForm.date) return
    setCreateTournamentLoading(true)
    try {
      await api('/api/v1/admin/tournaments', {
        method: 'POST',
        body: JSON.stringify(tournamentForm),
        token
      })
      const name = tournamentForm.name
      setShowCreateTournament(false)
      setTournamentForm({ name: '', date: '', month: getDefaultMonth() })
      loadTournaments()
      loadBudgets()
      showSuccess(`Турнир «${name}» добавлен`)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Ошибка')
    } finally {
      setCreateTournamentLoading(false)
    }
  }

  const handleSaveTournament = async () => {
    if (!token || !editingTournament) return
    try {
      await api(`/api/v1/admin/tournaments/${editingTournament.tournament_id}`, {
        method: 'PATCH',
        body: JSON.stringify(tournamentForm),
        token
      })
      setEditingTournament(null)
      loadTournaments()
      loadBudgets()
      showSuccess('Турнир обновлён')
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Ошибка')
    }
  }

  const handleDeleteTournament = async (t: AdminTournament) => {
    if (!confirm(`Удалить турнир «${t.name}» (${t.date})?`)) return
    if (!token) return
    try {
      await api(`/api/v1/admin/tournaments/${t.tournament_id}`, { method: 'DELETE', token })
      loadTournaments()
      loadBudgets()
      showSuccess('Турнир удалён')
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Ошибка')
    }
  }

  const handleEarningsRequest = async (paymentIds: number[]) => {
    if (!token || paymentIds.length === 0) return
    setEarningsRequestLoading(paymentIds[0])
    try {
      await api('/api/v1/admin/earnings/request', {
        method: 'POST',
        body: JSON.stringify({ payment_ids: paymentIds }),
        token
      })
      showSuccess('Запрос отправлен судье')
      loadEarnings()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Ошибка')
    } finally {
      setEarningsRequestLoading(null)
    }
  }

  const handleSetPaymentAmount = async (paymentId: number) => {
    const num = parseFloat(editingPaymentValue.replace(',', '.'))
    if (isNaN(num) || num < 0 || !token) return
    setSavingPaymentId(paymentId)
    try {
      await api(`/api/v1/admin/earnings/payment/${paymentId}`, {
        method: 'PATCH',
        body: JSON.stringify({ amount: num }),
        token
      })
      setEditingPaymentId(null)
      setEditingPaymentValue('')
      showSuccess('Заработок сохранён')
      loadEarnings()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Ошибка')
    } finally {
      setSavingPaymentId(null)
    }
  }

  const handleExportYear = async () => {
    if (!exportYear || !token) return
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8100'
    await downloadExport(
      `${apiUrl}/api/v1/admin/exports/year?year=${encodeURIComponent(exportYear)}`,
      `export_${exportYear}.xlsx`,
      'Экспорт за год скачан'
    )
  }

  const handleExportSeason = async () => {
    if (!exportSeason || !token) return
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8100'
    await downloadExport(
      `${apiUrl}/api/v1/admin/exports/season?season_key=${encodeURIComponent(exportSeason)}`,
      `export_season_${exportSeason}.xlsx`,
      'Экспорт за сезон скачан'
    )
  }

  const handleExportAll = async () => {
    if (!token) return
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8100'
    await downloadExport(
      `${apiUrl}/api/v1/admin/exports/all`,
      'export_all_seasons.xlsx',
      'Экспорт за все сезоны скачан'
    )
  }

  return (
    <div className="space-y-8">
      {successToast && (
        <div
          className="fixed left-1/2 top-4 z-50 -translate-x-1/2 animate-toast-in rounded-xl bg-emerald-500 px-6 py-4 text-white shadow-lg ring-1 ring-black/5"
          role="status"
          aria-live="polite"
        >
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white/20">
              <Check className="h-6 w-6" strokeWidth={2.5} />
            </div>
            <p className="font-medium">{successToast}</p>
          </div>
        </div>
      )}

      {resultToast && (
        <div
          className={`fixed left-1/2 top-4 z-50 -translate-x-1/2 animate-toast-in rounded-xl px-6 py-4 shadow-lg ring-1 ring-black/5 ${
            resultToast.type === 'approved'
              ? 'bg-emerald-500 text-white'
              : 'bg-red-500 text-white'
          }`}
          role="status"
          aria-live="polite"
        >
          <div className="flex items-center gap-3">
            {resultToast.type === 'approved' ? (
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white/20">
                <Check className="h-6 w-6" strokeWidth={2.5} />
              </div>
            ) : (
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white/20">
                <X className="h-6 w-6" strokeWidth={2.5} />
              </div>
            )}
            <div>
              <p className="font-semibold">
                {resultToast.type === 'approved' ? 'Заявка одобрена' : 'Заявка отклонена'}
              </p>
              <p className="text-sm opacity-90">
                {resultToast.userName} · {resultToast.tournamentName}
              </p>
            </div>
          </div>
        </div>
      )}

      <h1 className="text-xl font-semibold text-slate-800 md:text-2xl">Админ-панель</h1>

      <nav className="flex flex-wrap gap-2 border-b border-slate-200 pb-3" aria-label="Разделы админки">
        {[
          { id: 'registrations' as const, label: 'Заявки', icon: ClipboardList },
          { id: 'tournaments' as const, label: 'Турниры', icon: Trophy },
          { id: 'users' as const, label: 'Пользователи', icon: Users },
          { id: 'budgets' as const, label: 'Бюджеты', icon: DollarSign },
          { id: 'earnings' as const, label: 'Заработок судей', icon: Wallet },
          { id: 'broadcast' as const, label: 'Рассылка', icon: Send },
          { id: 'export' as const, label: 'Экспорт', icon: FileSpreadsheet }
        ].map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex min-h-[44px] items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition ${
              activeTab === id
                ? 'bg-slate-800 text-white'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </nav>

      {activeTab === 'broadcast' && (
      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 flex items-center gap-2 font-medium text-slate-800">
          <Send className="h-5 w-5" />
          Рассылка в Telegram
        </h2>
        <form onSubmit={handleBroadcast} className="space-y-4">
          <textarea
            value={broadcastMsg}
            onChange={(e) => setBroadcastMsg(e.target.value)}
            placeholder="Сообщение для всех судей..."
            rows={4}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-800 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
            disabled={broadcastLoading}
          />
          <button
            type="submit"
            disabled={broadcastLoading}
            className="rounded-lg bg-slate-800 px-4 py-2 font-medium text-white hover:bg-slate-700 disabled:opacity-50"
          >
            {broadcastLoading ? 'Отправка...' : 'Отправить'}
          </button>
          {broadcastResult && (
            <p className="text-sm text-slate-600">
              Отправлено: {broadcastResult.ok} из {broadcastResult.total}, ошибок: {broadcastResult.fail}
            </p>
          )}
        </form>
      </section>
      )}

      {activeTab === 'tournaments' && (
      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="flex items-center gap-2 font-medium text-slate-800">
            <Trophy className="h-5 w-5" />
            Турниры
          </h2>
          <div className="flex flex-wrap items-center gap-2">
            <MonthFilter value={tournamentsMonthFilter} onChange={setTournamentsMonthFilter} />
            <button
              onClick={() => {
                setTournamentForm({ name: '', date: '', month: getDefaultMonth() })
                setShowCreateTournament(true)
              }}
              className="inline-flex min-h-[44px] items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-700"
            >
              <PlusCircle className="h-4 w-4" />
              Создать турнир
            </button>
          </div>
        </div>
        <input
          type="search"
          placeholder="Поиск: любые буквы подряд (андр, никол...)"
          value={tournamentsSearch}
          onChange={(e) => setTournamentsSearch(e.target.value)}
          className="mb-3 min-h-[44px] w-full max-w-xs rounded-lg border border-slate-300 px-3 py-2.5 text-slate-800 sm:w-64"
        />
        {tournamentsLoading ? (
          <div className="py-4 text-center text-slate-500">Загрузка...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="px-2 py-2 text-left">Название</th>
                  <th className="px-2 py-2 text-left">Дата</th>
                  <th className="px-2 py-2 text-left">Месяц</th>
                  <th className="px-2 py-2 text-right">Действия</th>
                </tr>
              </thead>
              <tbody>
                {tournaments.map((t) => (
                  <tr key={t.tournament_id} className="border-b border-slate-100">
                    <td className="px-2 py-2">{t.name}</td>
                    <td className="px-2 py-2 text-slate-600">{t.date}</td>
                    <td className="px-2 py-2 text-slate-600">{t.month}</td>
                    <td className="px-2 py-2 text-right">
                      <button
                        onClick={() => {
                          setEditingTournament(t)
                          const parts = t.date.split('.')
                          const dateStr = parts.length === 3 ? `${parts[2]}-${parts[1]}-${parts[0]}` : t.date
                          setTournamentForm({ name: t.name, date: dateStr, month: t.month })
                        }}
                        className="mr-2 rounded px-2 py-1 text-slate-600 hover:bg-slate-100"
                        title="Изменить"
                      >
                        <Pencil className="inline h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteTournament(t)}
                        className="rounded px-2 py-1 text-red-600 hover:bg-red-50"
                        title="Удалить"
                      >
                        <Trash2 className="inline h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {tournaments.length === 0 && <p className="py-4 text-center text-slate-500">Нет турниров</p>}
          </div>
        )}
      </section>
      )}

      {activeTab === 'users' && (
      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="flex items-center gap-2 font-medium text-slate-800">
            <Users className="h-5 w-5" />
            Пользователи
          </h2>
          <div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row sm:items-center">
            <SeasonFilter value={statsSeason} onChange={setStatsSeason} seasons={seasonOptions} />
            <input
              type="search"
              placeholder="Поиск: имя, фамилия, функция, email..."
              value={usersSearch}
              onChange={(e) => setUsersSearch(e.target.value)}
              className="min-h-[44px] w-full rounded-lg border border-slate-300 px-3 py-2.5 text-slate-800 sm:w-64"
            />
          </div>
        </div>
        <p className="mb-3 text-xs text-slate-500">
          Статистика заявок за сезон: <strong>{selectedSeasonLabel}</strong>
        </p>
        {usersLoading ? (
          <div className="py-4 text-center text-slate-500">Загрузка...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="px-2 py-2 text-left">Имя</th>
                  <th className="px-2 py-2 text-left">Функция</th>
                  <th className="px-2 py-2 text-left">Категория</th>
                  <th className="px-2 py-2 text-left">Email</th>
                  <th className="px-2 py-2 text-left" title={`Заявки за сезон ${selectedSeasonLabel}`}>Заявки</th>
                  <th className="px-2 py-2 text-left" title={`Отмены после одобрения за сезон ${selectedSeasonLabel}`}>Отказы после ✓</th>
                  <th className="px-2 py-2 text-left">Статус</th>
                  <th className="px-2 py-2 text-right">Действия</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.user_id} className={`border-b border-slate-100 ${u.is_blocked ? 'bg-red-50' : ''}`}>
                    <td className="px-2 py-2">{u.first_name} {u.last_name}</td>
                    <td className="px-2 py-2 text-slate-600">{u.function}</td>
                    <td className="px-2 py-2 text-slate-600">{u.category}</td>
                    <td className="px-2 py-2 text-slate-600">{u.email || '—'}</td>
                    <td className="px-2 py-2" title="Одобрено / На рассмотрении / Отклонено · % одобрения · % отказов">
                      {(u.regs_total ?? 0) > 0 ? (
                        <span className="text-slate-700">
                          <span className="text-emerald-600 font-medium">{u.regs_approved ?? 0}</span>
                          <span className="text-slate-400"> / </span>
                          <span className="text-amber-600">{u.regs_pending ?? 0}</span>
                          <span className="text-slate-400"> / </span>
                          <span className="text-red-600 font-medium">{u.regs_rejected ?? 0}</span>
                          <span className="ml-1 text-xs text-slate-500">
                            ({u.approved_pct ?? 0}% ✓ · {u.rejected_pct ?? 0}% ✕)
                          </span>
                        </span>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>
                    <td className="px-2 py-2 text-slate-700">
                      {(u.season_refusals ?? 0) > 0 ? (
                        <span>
                          <span className="font-medium text-rose-700">{u.season_refusals}</span>
                          <span className="ml-1 text-xs text-slate-500">
                            ({u.season_refusal_pct ?? 0}% из {u.season_approved_assignments ?? 0})
                          </span>
                        </span>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>
                    <td className="px-2 py-2">
                      {u.is_blocked ? <span className="rounded bg-red-100 px-2 py-0.5 text-xs text-red-800">Заблокирован</span> : <span className="text-slate-500">Активен</span>}
                    </td>
                    <td className="px-2 py-2 text-right">
                      <button
                        onClick={() => {
                          setEditingUser(u)
                          setUserForm({ first_name: u.first_name, last_name: u.last_name, function: u.function, category: u.category, is_blocked: u.is_blocked })
                        }}
                        className="rounded px-2 py-1 text-slate-600 hover:bg-slate-100"
                        title="Изменить"
                      >
                        <Pencil className="inline h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {users.length === 0 && <p className="py-4 text-center text-slate-500">Нет пользователей</p>}
          </div>
        )}
      </section>
      )}

      {activeTab === 'budgets' && (
      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="flex items-center gap-2 font-medium text-slate-800">
            <DollarSign className="h-5 w-5" />
            Бюджеты турниров
          </h2>
          <MonthFilter value={budgetsMonthFilter} onChange={setBudgetsMonthFilter} />
        </div>
        {budgetSummary && (
          <div className="mb-4 flex flex-wrap gap-4 rounded-lg bg-slate-50 p-3">
            <span>Общая прибыль: <strong>{budgetSummary.total_profit ?? 0} ₽</strong></span>
            <span>За месяц: <strong>{budgetSummary.monthly_profit ?? 0} ₽</strong></span>
            <span>За сезон: <strong>{budgetSummary.seasonal_profit ?? 0} ₽</strong></span>
            <span>Турниров с прибылью: <strong>{budgetSummary.tournaments_count ?? 0}</strong></span>
            {budgets.filter((b) => !b.budget_set).length > 0 && (
              <span className="rounded bg-amber-100 px-2 py-0.5 text-amber-800">
                Без бюджета: <strong>{budgets.filter((b) => !b.budget_set).length}</strong>
              </span>
            )}
          </div>
        )}
        {budgetsLoading ? (
          <div className="py-4 text-center text-slate-500">Загрузка...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="px-2 py-2 text-left">Турнир</th>
                  <th className="px-2 py-2 text-left">Дата</th>
                  <th className="px-2 py-2 text-right">Бюджет</th>
                  <th className="px-2 py-2 text-right">Судьи</th>
                  <th className="px-2 py-2 text-right">Прибыль</th>
                  <th className="px-2 py-2"></th>
                </tr>
              </thead>
              <tbody>
                {budgets.map((b) => (
                  <tr
                    key={b.tournament_id}
                    className={`border-b border-slate-100 ${!b.budget_set ? 'bg-amber-50' : ''}`}
                  >
                    <td className="px-2 py-2">
                      <span className="font-medium">{b.tournament_name}</span>
                      {!b.budget_set && (
                        <span className="ml-2 rounded bg-amber-200 px-1.5 py-0.5 text-xs text-amber-900">
                          Бюджет не задан
                        </span>
                      )}
                    </td>
                    <td className="px-2 py-2 text-slate-600">
                      {typeof b.tournament_date === 'string' ? b.tournament_date : String(b.tournament_date).slice(0, 10)}
                    </td>
                    <td className="px-2 py-2 text-right">
                      {b.budget_set ? `${b.total_budget} ₽` : '—'}
                    </td>
                    <td className="px-2 py-2 text-right">
                      {b.budget_set ? `${b.judges_payment} ₽` : '—'}
                    </td>
                    <td className="px-2 py-2 text-right">
                      {b.budget_set ? `${b.admin_profit} ₽` : '—'}
                    </td>
                    <td className="px-2 py-2">
                      {editingBudget?.id === b.tournament_id ? (
                        <div className="flex gap-1">
                          <input
                            type="number"
                            value={editingBudget.value}
                            onChange={(e) => setEditingBudget({ ...editingBudget, value: e.target.value })}
                            placeholder="Сумма"
                            min={1}
                            className="w-24 rounded border px-2 py-1"
                          />
                          <button
                            onClick={() => handleSetBudget(b.tournament_id, editingBudget.value)}
                            className="rounded bg-emerald-600 px-2 py-1 text-white text-xs"
                          >
                            OK
                          </button>
                          <button
                            onClick={() => setEditingBudget(null)}
                            className="rounded border px-2 py-1 text-xs"
                          >
                            Отмена
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => setEditingBudget({ id: b.tournament_id, value: String(b.total_budget || '') })}
                          className={`text-xs ${!b.budget_set ? 'font-medium text-amber-700 hover:text-amber-900' : 'text-slate-500 hover:text-slate-700'}`}
                        >
                          {!b.budget_set ? 'Задать бюджет' : 'Изменить'}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {budgets.length === 0 && (
              <p className="py-4 text-center text-slate-500">Нет бюджетов</p>
            )}
          </div>
        )}
      </section>
      )}

      {activeTab === 'earnings' && (
      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 flex items-center gap-2 font-medium text-slate-800">
          <Wallet className="h-5 w-5" />
          Заработок судей
        </h2>
        <input
          type="search"
          placeholder="Поиск: имя судьи, турнир..."
          value={earningsSearch}
          onChange={(e) => setEarningsSearch(e.target.value)}
          aria-label="Поиск"
          className="mb-4 min-h-[44px] w-full max-w-md rounded-lg border border-slate-300 px-3 py-2.5 text-slate-800 placeholder:text-slate-400 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
        />
        {earningsLoading ? (
          <div className="py-4 text-center text-slate-500">Загрузка...</div>
        ) : (
          <div className="space-y-2">
            {earnings.map((j, idx) => {
              const rank = idx + 1
              const rankLabel = rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : `#${rank}`
              const paidCount = j.with_amount
              const statusLabel = paidCount >= 50 ? '🥇 Золотой судья' : paidCount >= 25 ? '🥈 Серебряный судья' : paidCount >= 10 ? '🥉 Бронзовый судья' : '⭐ Начинающий судья'
              const progressToNext = paidCount < 10 ? { current: paidCount, target: 10, next: 'Бронзовый' } : paidCount < 25 ? { current: paidCount, target: 25, next: 'Серебряный' } : paidCount < 50 ? { current: paidCount, target: 50, next: 'Золотой' } : null
              const isExpanded = expandedEarningsIds.has(j.user_id)
              const isSumExpanded = expandedEarningsSumIds.has(j.user_id)
              const monthlyMap = j.tournaments.reduce<Record<string, { sum: number; count: number }>>((acc, t) => {
                if (t.amount == null) return acc
                const m = t.tournament_date?.slice(3, 10) || ''
                if (!acc[m]) acc[m] = { sum: 0, count: 0 }
                acc[m].sum += t.amount
                acc[m].count += 1
                return acc
              }, {})
              const seasonSortKey = (mm: string, yy: string) => {
                const m = parseInt(mm || '1', 10)
                const y = parseInt(yy || '0', 10)
                const seasonYear = m >= 7 ? y : y - 1
                const seasonMonth = (m - 7 + 12) % 12
                return [seasonYear, seasonMonth]
              }
              const monthlyList = Object.entries(monthlyMap)
                .sort((a, b) => {
                  const [mmA, yyA] = a[0].split('.')
                  const [mmB, yyB] = b[0].split('.')
                  const [syA, smA] = seasonSortKey(mmA, yyA)
                  const [syB, smB] = seasonSortKey(mmB, yyB)
                  return syA !== syB ? syA - syB : smA - smB
                })
                .map(([k, v]) => {
                  const [mm, yy] = k.split('.')
                  const monthName = MONTH_NAMES[parseInt(mm || '1', 10) - 1] || mm
                  return { label: `${monthName} ${yy}`, ...v }
                })
              return (
                <div key={j.user_id} className="overflow-hidden rounded-lg border border-slate-200">
                  <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-50 px-4 py-3">
                    <div className="flex flex-1 items-center gap-3">
                      <button
                        type="button"
                        onClick={() => setExpandedEarningsIds((p) => { const n = new Set(p); if (n.has(j.user_id)) n.delete(j.user_id); else n.add(j.user_id); return n })}
                        className="flex items-center gap-2 text-left"
                      >
                        {isExpanded ? <ChevronDown className="h-5 w-5 text-slate-500" /> : <ChevronRight className="h-5 w-5 text-slate-500" />}
                        <span className="font-medium text-slate-800">{j.user_name}</span>
                        {(j.function || j.category) && (
                          <span className="text-xs text-slate-500">
                            {[j.function, j.category].filter(Boolean).join(' · ')}
                          </span>
                        )}
                      </button>
                      <span className="rounded bg-amber-100 px-2 py-0.5 text-sm font-medium text-amber-800" title="Рейтинг по заработку">
                        {rankLabel}
                      </span>
                      <span className="rounded bg-slate-200 px-2 py-0.5 text-sm font-medium text-slate-700" title="Статус по количеству турниров">
                        {statusLabel}
                      </span>
                      {progressToNext && (
                        <span className="text-xs text-slate-500" title={`До ${progressToNext.next} судьи`}>
                          {progressToNext.current}/{progressToNext.target}
                        </span>
                      )}
                      <span className="text-sm text-slate-500">
                        Турниров: {j.total_tournaments} · Указано: {j.with_amount} · Не указано: {j.without_amount}
                      </span>
                      {j.without_amount > 0 && (
                        <button
                          onClick={() => handleEarningsRequest(j.without_amount_list.map((x) => x.payment_id))}
                          disabled={earningsRequestLoading !== null}
                          className="inline-flex items-center gap-1 rounded-lg border border-amber-300 bg-amber-50 px-2 py-1 text-sm text-amber-800 hover:bg-amber-100 disabled:opacity-50"
                        >
                          <Mail className="h-4 w-4" />
                          {earningsRequestLoading !== null && j.without_amount_list.some((x) => x.payment_id === earningsRequestLoading) ? 'Отправка...' : 'Отправить запрос'}
                        </button>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => setExpandedEarningsSumIds((p) => { const n = new Set(p); if (n.has(j.user_id)) n.delete(j.user_id); else n.add(j.user_id); return n })}
                      className="rounded-lg bg-emerald-100 px-3 py-1.5 text-sm font-medium text-emerald-800 hover:bg-emerald-200"
                    >
                      {j.total_amount.toFixed(0)} ₽
                    </button>
                  </div>
                  {isSumExpanded && monthlyList.length > 0 && (
                    <div className="border-t border-slate-200 bg-emerald-50/50 px-4 py-3">
                      <p className="mb-2 text-sm font-medium text-slate-700">Разбивка по месяцам</p>
                      <div className="flex flex-wrap gap-3">
                        {monthlyList.map(({ label, sum, count }) => (
                          <span key={label} className="rounded bg-white px-3 py-1.5 text-sm shadow-sm">
                            {label} — {sum.toFixed(0)} ₽ ({count} турн.)
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {isExpanded && (
                    <div className="border-t border-slate-200 bg-white">
                      {j.tournaments.map((t) => (
                        <div
                          key={t.payment_id}
                          className="flex flex-col gap-2 border-b border-slate-100 px-4 py-3 last:border-b-0 sm:flex-row sm:items-center sm:justify-between"
                        >
                          <div className="pl-8">
                            <p className="font-medium text-slate-800">{t.tournament_name}</p>
                            <p className="text-sm text-slate-500">
                              {t.tournament_date} · {t.tournament_month}
                            </p>
                          </div>
                          <div className="flex flex-wrap items-center gap-2 pl-8">
                            {editingPaymentId === t.payment_id ? (
                              <>
                                <input
                                  type="number"
                                  min={0}
                                  step={100}
                                  value={editingPaymentValue}
                                  onChange={(e) => setEditingPaymentValue(e.target.value)}
                                  placeholder="Сумма ₽"
                                  className="w-28 rounded border border-slate-300 px-2 py-1.5 text-sm"
                                  aria-label="Сумма заработка"
                                />
                                <button
                                  onClick={() => handleSetPaymentAmount(t.payment_id)}
                                  disabled={savingPaymentId !== null}
                                  className="rounded bg-emerald-600 px-2 py-1.5 text-sm text-white hover:bg-emerald-700 disabled:opacity-50"
                                >
                                  {savingPaymentId === t.payment_id ? 'Сохранение...' : 'Сохранить'}
                                </button>
                                <button
                                  onClick={() => { setEditingPaymentId(null); setEditingPaymentValue('') }}
                                  disabled={savingPaymentId !== null}
                                  className="rounded border px-2 py-1.5 text-sm"
                                >
                                  Отмена
                                </button>
                              </>
                            ) : t.amount != null ? (
                              <>
                                <span className="font-medium text-emerald-700">{t.amount.toFixed(0)} ₽</span>
                                <button
                                  onClick={() => { setEditingPaymentId(t.payment_id); setEditingPaymentValue(String(t.amount)) }}
                                  className="inline-flex items-center gap-1 rounded border border-slate-300 px-2 py-1 text-xs text-slate-600 hover:bg-slate-50"
                                  aria-label="Изменить"
                                >
                                  <Pencil className="h-4 w-4" />
                                  Изменить
                                </button>
                              </>
                            ) : (
                              <>
                                <button
                                  onClick={() => { setEditingPaymentId(t.payment_id); setEditingPaymentValue('') }}
                                  className="inline-flex items-center gap-1 rounded border border-slate-300 px-2 py-1 text-xs text-slate-600 hover:bg-slate-50"
                                  aria-label="Ввести"
                                >
                                  <Pencil className="h-4 w-4" />
                                  Ввести
                                </button>
                                <button
                                  onClick={() => handleEarningsRequest([t.payment_id])}
                                  disabled={earningsRequestLoading !== null}
                                  className="inline-flex items-center gap-1 rounded-lg border border-amber-300 bg-amber-50 px-2 py-1 text-sm text-amber-800 hover:bg-amber-100 disabled:opacity-50"
                                >
                                  <Mail className="h-4 w-4" />
                                  {earningsRequestLoading === t.payment_id ? 'Отправка...' : 'Отправить запрос'}
                                </button>
                              </>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
            {earnings.length === 0 && (
              <p className="py-4 text-center text-slate-500">Нет данных</p>
            )}
          </div>
        )}
      </section>
      )}

      {activeTab === 'registrations' && (
      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="flex items-center gap-2 font-medium text-slate-800">
            <ClipboardList className="h-5 w-5" />
            Заявки
          </h2>
          <MonthFilter value={regsMonthFilter} onChange={setRegsMonthFilter} />
        </div>
        <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <input
            type="search"
            placeholder="Поиск: имя, турнир, месяц..."
            value={regsSearch}
            onChange={(e) => setRegsSearch(e.target.value)}
            aria-label="Поиск заявок"
            className="min-h-[44px] w-full rounded-lg border border-slate-300 px-3 py-2.5 text-slate-800 placeholder:text-slate-400 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500 sm:w-64"
          />
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setRegsFilter('pending')}
              className={`min-h-[44px] rounded-lg px-4 py-2.5 text-sm ${regsFilter === 'pending' ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-600'}`}
            >
              На рассмотрении
            </button>
            <button
              onClick={() => setRegsFilter('approved')}
              className={`min-h-[44px] rounded-lg px-4 py-2.5 text-sm ${regsFilter === 'approved' ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-600'}`}
            >
              Одобренные
            </button>
            <button
              onClick={() => setRegsFilter('rejected')}
              className={`min-h-[44px] rounded-lg px-4 py-2.5 text-sm ${regsFilter === 'rejected' ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-600'}`}
            >
              Отклонённые
            </button>
            <button
              onClick={() => setRegsFilter('')}
              className={`min-h-[44px] rounded-lg px-4 py-2.5 text-sm ${!regsFilter ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-600'}`}
            >
              Все
            </button>
          </div>
        </div>
        {refusalsStats?.season && (
          <div className="mb-4 rounded-lg border border-rose-200 bg-rose-50/40 p-4">
            <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <h3 className="text-sm font-semibold uppercase tracking-wide text-rose-800">
                Отказы после одобрения
              </h3>
              <SeasonFilter value={statsSeason} onChange={setStatsSeason} seasons={seasonOptions} />
            </div>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
              <div className="rounded-lg border border-rose-200 bg-white px-3 py-2">
                <p className="text-xs text-slate-500">Сезон</p>
                <p className="text-sm font-medium text-slate-800">
                  {refusalsStats.season.label || selectedSeasonLabel}
                  {refusalsStats.season.start !== '—' && (
                    <span className="block text-xs text-slate-500">
                      {refusalsStats.season.start} - {refusalsStats.season.end}
                    </span>
                  )}
                </p>
              </div>
              <div className="rounded-lg border border-rose-200 bg-white px-3 py-2">
                <p className="text-xs text-slate-500">Отказов после одобрения</p>
                <p className="text-lg font-semibold text-rose-700">{refusalsStats.season.refusals}</p>
              </div>
              <div className="rounded-lg border border-rose-200 bg-white px-3 py-2">
                <p className="text-xs text-slate-500">Доля от всех одобрений</p>
                <p className="text-lg font-semibold text-slate-800">
                  {refusalsStats.season.refusal_pct}%
                </p>
                <p className="text-xs text-slate-500">
                  из {refusalsStats.season.approved_assignments} одобрений
                </p>
              </div>
              <div className="rounded-lg border border-rose-200 bg-white px-3 py-2">
                <p className="text-xs text-slate-500">Ответственность</p>
                <p className="text-sm font-semibold text-slate-800">
                  {refusalsStats.season.responsibility_label} ({refusalsStats.season.responsibility_score}/100)
                </p>
              </div>
            </div>
            {refusalsStats.monthly.length > 0 && (
              <div className="mt-4 overflow-x-auto">
                <p className="mb-2 text-xs font-medium uppercase tracking-wide text-rose-700">По месяцам</p>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-rose-200">
                      <th className="px-2 py-2 text-left">Месяц</th>
                      <th className="px-2 py-2 text-right">Отказов после одобрения</th>
                    </tr>
                  </thead>
                  <tbody>
                    {refusalsStats.monthly.map((row) => (
                      <tr key={row.month_key} className="border-b border-rose-100 last:border-b-0">
                        <td className="px-2 py-2 text-slate-700">{row.month}</td>
                        <td className="px-2 py-2 text-right text-rose-700">{row.refusals}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {(refusalsStats.by_judge?.length ?? 0) > 0 && (
              <div className="mt-4 overflow-x-auto">
                <p className="mb-2 text-xs font-medium uppercase tracking-wide text-rose-700">По судьям</p>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-rose-200">
                      <th className="px-2 py-2 text-left">Судья</th>
                      <th className="px-2 py-2 text-right">Отказов</th>
                      <th className="px-2 py-2 text-right">Одобрено за сезон</th>
                      <th className="px-2 py-2 text-right">% от одобренных</th>
                    </tr>
                  </thead>
                  <tbody>
                    {refusalsStats.by_judge!.map((row) => (
                      <tr key={row.user_id} className="border-b border-rose-100 last:border-b-0">
                        <td className="px-2 py-2 text-slate-700">{row.user_name}</td>
                        <td className="px-2 py-2 text-right text-rose-700">{row.refusals}</td>
                        <td className="px-2 py-2 text-right text-slate-700">{row.approved_assignments}</td>
                        <td className="px-2 py-2 text-right text-slate-700">{row.refusal_pct}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
        {regsLoading ? (
          <div className="py-4 text-center text-slate-500">Загрузка...</div>
        ) : (
          <div className="space-y-2">
            {regsByTournament.map(({ tournament_id, tournament_name, tournament_date, tournament_month, regs }) => {
              const isExpanded = expandedTournamentIds.has(tournament_id)
              const pendingCount = regs.filter((r) => r.status === 'pending').length
              return (
                <div key={tournament_id} className="overflow-hidden rounded-lg border border-slate-200">
                  <button
                    type="button"
                    onClick={() => toggleTournamentExpand(tournament_id)}
                    className="flex w-full items-center justify-between gap-3 bg-slate-50 px-4 py-3 text-left transition hover:bg-slate-100"
                    aria-expanded={isExpanded}
                  >
                    <div className="flex min-w-0 flex-1 items-center gap-3">
                      {isExpanded ? (
                        <ChevronDown className="h-5 w-5 shrink-0 text-slate-500" />
                      ) : (
                        <ChevronRight className="h-5 w-5 shrink-0 text-slate-500" />
                      )}
                      <div className="min-w-0">
                        <p className="font-medium text-slate-800">{tournament_name}</p>
                        <p className="text-sm text-slate-500">
                          {tournament_date} · {tournament_month} · {regs.length} {regs.length === 1 ? 'заявка' : regs.length < 5 ? 'заявки' : 'заявок'}
                          {pendingCount > 0 && (
                            <span className="ml-1 text-amber-600">({pendingCount} на рассмотрении)</span>
                          )}
                        </p>
                      </div>
                    </div>
                  </button>
                  {isExpanded && (
                    <div className="border-t border-slate-200 bg-white">
                      {regs.map((r) => (
                        <div
                          key={r.registration_id}
                          className={`group flex flex-col gap-3 border-b border-slate-100 px-4 py-3 last:border-b-0 sm:flex-row sm:items-center sm:justify-start sm:gap-6 xl:gap-8 ${
                            r.status === 'approved'
                              ? 'bg-green-50 sm:hover:bg-green-100/80'
                              : r.status === 'rejected'
                                ? 'bg-red-50 sm:hover:bg-red-100/80'
                                : 'sm:hover:bg-slate-50 sm:hover:shadow-[inset_0_0_0_1px_rgb(203_213_225)]'
                          } transition-colors`}
                        >
                          <div className="min-w-0 shrink-0 pl-8 sm:max-w-[min(40%,28rem)]">
                            <p className="font-medium text-slate-800">{r.user_name}</p>
                            <span className={`inline-block rounded px-2 py-0.5 text-xs ${
                              r.status === 'approved' ? 'bg-green-100 text-green-800' :
                              r.status === 'rejected' ? 'bg-red-100 text-red-800' :
                              'bg-amber-100 text-amber-800'
                            }`}>
                              {r.status === 'pending' ? 'На рассмотрении' : r.status === 'approved' ? 'Одобрена' : 'Отклонена'}
                            </span>
                          </div>
                          {r.status === 'pending' && (
                            <div className="flex shrink-0 flex-col gap-2 pl-8 sm:flex-row sm:pl-0 sm:rounded-lg sm:p-0.5 sm:transition-shadow sm:group-hover:shadow-[0_0_0_2px_rgb(148_163_184)]">
                              <button
                                type="button"
                                onClick={() => handleApprove(r)}
                                className="inline-flex min-h-[44px] items-center justify-center gap-1 rounded-lg bg-green-600 px-4 py-2.5 text-sm text-white hover:bg-green-700"
                              >
                                <Check className="h-4 w-4" />
                                Одобрить
                              </button>
                              <button
                                type="button"
                                onClick={() => handleReject(r)}
                                className="inline-flex min-h-[44px] items-center justify-center gap-1 rounded-lg border border-red-300 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50"
                              >
                                <X className="h-4 w-4" />
                                Отклонить
                              </button>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
            {regsByTournament.length === 0 && (
              <p className="py-4 text-center text-slate-500">Нет заявок</p>
            )}
          </div>
        )}
      </section>
      )}

      {activeTab === 'export' && (
      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 flex items-center gap-2 font-medium text-slate-800">
          <FileSpreadsheet className="h-5 w-5" />
          Экспорт в Excel
        </h2>
        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap items-center gap-2">
            <SeasonFilter value={exportSeason} onChange={setExportSeason} seasons={seasonOptions} />
            <button
              onClick={handleExportSeason}
              disabled={!exportSeason || exportLoading}
              className="rounded-lg bg-slate-800 px-4 py-2 text-white hover:bg-slate-700 disabled:opacity-50"
            >
              {exportLoading ? '...' : 'Экспорт за сезон'}
            </button>
            <button
              onClick={handleExportAll}
              disabled={exportLoading}
              className="rounded-lg border border-slate-300 px-4 py-2 text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            >
              {exportLoading ? '...' : 'Экспорт за все сезоны'}
            </button>
          </div>
          <div className="flex flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <input
              type="text"
              placeholder="Месяц (напр. Январь)"
              value={exportMonth}
              onChange={(e) => setExportMonth(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2"
            />
            <button
              onClick={handleExportMonth}
              disabled={!exportMonth || exportLoading}
              className="rounded-lg bg-slate-800 px-4 py-2 text-white hover:bg-slate-700 disabled:opacity-50"
            >
              {exportLoading ? '...' : 'Экспорт по месяцу'}
            </button>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="number"
              placeholder="Год (напр. 2024)"
              value={exportYear}
              onChange={(e) => setExportYear(e.target.value)}
              className="w-28 rounded-lg border border-slate-300 px-3 py-2"
            />
            <button
              onClick={handleExportYear}
              disabled={!exportYear || exportLoading}
              className="rounded-lg bg-slate-800 px-4 py-2 text-white hover:bg-slate-700 disabled:opacity-50"
            >
              {exportLoading ? '...' : 'Экспорт по году'}
            </button>
          </div>
          </div>
        </div>
      </section>
      )}

      {editingUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={() => setEditingUser(null)}>
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <h3 className="mb-4 font-semibold text-slate-800">Редактировать пользователя</h3>
            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-sm text-slate-600">Имя</label>
                <input value={userForm.first_name} onChange={(e) => setUserForm((f) => ({ ...f, first_name: e.target.value }))} className="w-full rounded-lg border px-3 py-2" />
              </div>
              <div>
                <label className="mb-1 block text-sm text-slate-600">Фамилия</label>
                <input value={userForm.last_name} onChange={(e) => setUserForm((f) => ({ ...f, last_name: e.target.value }))} className="w-full rounded-lg border px-3 py-2" />
              </div>
              <div>
                <label className="mb-1 block text-sm text-slate-600">Функция</label>
                <input value={userForm.function} onChange={(e) => setUserForm((f) => ({ ...f, function: e.target.value }))} className="w-full rounded-lg border px-3 py-2" />
              </div>
              <div>
                <label className="mb-1 block text-sm text-slate-600">Категория</label>
                <input value={userForm.category} onChange={(e) => setUserForm((f) => ({ ...f, category: e.target.value }))} className="w-full rounded-lg border px-3 py-2" />
              </div>
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={userForm.is_blocked} onChange={(e) => setUserForm((f) => ({ ...f, is_blocked: e.target.checked }))} />
                <span className="text-sm text-red-600">Заблокировать</span>
              </label>
            </div>
            <div className="mt-4 flex gap-2">
              <button onClick={handleSaveUser} className="rounded-lg bg-slate-800 px-4 py-2 text-white hover:bg-slate-700">Сохранить</button>
              <button onClick={() => setEditingUser(null)} className="rounded-lg border px-4 py-2">Отмена</button>
            </div>
          </div>
        </div>
      )}

      {showCreateTournament && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={() => setShowCreateTournament(false)}>
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <h3 className="mb-4 font-semibold text-slate-800">Создать турнир</h3>
            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-sm text-slate-600">Название</label>
                <input value={tournamentForm.name} onChange={(e) => setTournamentForm((f) => ({ ...f, name: e.target.value }))} placeholder="Арена Плей Север" className="w-full rounded-lg border px-3 py-2" />
              </div>
              <div>
                <label className="mb-1 block text-sm text-slate-600">Дата</label>
                <input
                  type="date"
                  value={tournamentForm.date}
                  onChange={(e) => {
                    const dateVal = e.target.value
                    setTournamentForm((f) => ({ ...f, date: dateVal, month: getMonthFromDate(dateVal) }))
                  }}
                  className="w-full rounded-lg border px-3 py-2"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm text-slate-600">Месяц (автоматически из даты)</label>
                <select value={tournamentForm.month || getDefaultMonth()} onChange={(e) => setTournamentForm((f) => ({ ...f, month: e.target.value }))} className="w-full rounded-lg border px-3 py-2">
                  {MONTH_NAMES.map((m) => <option key={m} value={m}>{m}</option>)}
                </select>
              </div>
            </div>
            <div className="mt-4 flex gap-2">
              <button
                onClick={handleCreateTournament}
                disabled={createTournamentLoading}
                className="rounded-lg bg-emerald-600 px-4 py-2 text-white hover:bg-emerald-700 disabled:opacity-60"
              >
                {createTournamentLoading ? 'Создание...' : 'Создать'}
              </button>
              <button onClick={() => setShowCreateTournament(false)} disabled={createTournamentLoading} className="rounded-lg border px-4 py-2 disabled:opacity-60">Отмена</button>
            </div>
          </div>
        </div>
      )}

      {editingTournament && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={() => setEditingTournament(null)}>
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <h3 className="mb-4 font-semibold text-slate-800">Изменить турнир</h3>
            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-sm text-slate-600">Название</label>
                <input value={tournamentForm.name} onChange={(e) => setTournamentForm((f) => ({ ...f, name: e.target.value }))} className="w-full rounded-lg border px-3 py-2" />
              </div>
              <div>
                <label className="mb-1 block text-sm text-slate-600">Дата</label>
                <input
                  type="date"
                  value={tournamentForm.date}
                  onChange={(e) => {
                    const dateVal = e.target.value
                    setTournamentForm((f) => ({ ...f, date: dateVal, month: getMonthFromDate(dateVal) }))
                  }}
                  className="w-full rounded-lg border px-3 py-2"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm text-slate-600">Месяц (автоматически из даты)</label>
                <select value={tournamentForm.month} onChange={(e) => setTournamentForm((f) => ({ ...f, month: e.target.value }))} className="w-full rounded-lg border px-3 py-2">
                  {MONTH_NAMES.map((m) => <option key={m} value={m}>{m}</option>)}
                </select>
              </div>
            </div>
            <div className="mt-4 flex gap-2">
              <button onClick={handleSaveTournament} className="rounded-lg bg-slate-800 px-4 py-2 text-white hover:bg-slate-700">Сохранить</button>
              <button onClick={() => setEditingTournament(null)} className="rounded-lg border px-4 py-2">Отмена</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
