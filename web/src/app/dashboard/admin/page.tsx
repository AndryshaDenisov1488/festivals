'use client'

import { useEffect, useMemo, useState } from 'react'
import { api } from '@/lib/api'
import { Send, DollarSign, FileSpreadsheet, ClipboardList, Check, X, Users, Trophy, PlusCircle, Pencil, Trash2, ChevronDown, ChevronRight } from 'lucide-react'
import MonthFilter, { type MonthFilterValue } from '@/components/MonthFilter'

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
}

type AdminTournament = {
  tournament_id: number
  name: string
  date: string
  month: string
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
  const [regsFilter, setRegsFilter] = useState<'pending' | 'approved' | 'rejected' | ''>('pending')
  const [regsMonthFilter, setRegsMonthFilter] = useState<MonthFilterValue>('future')
  const [regsSearch, setRegsSearch] = useState('')
  const [expandedTournamentIds, setExpandedTournamentIds] = useState<Set<number>>(new Set())
  const [budgetsMonthFilter, setBudgetsMonthFilter] = useState<MonthFilterValue>('future')

  const [exportMonth, setExportMonth] = useState('')
  const [exportYear, setExportYear] = useState('')
  const [exportLoading, setExportLoading] = useState(false)

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
  const [activeTab, setActiveTab] = useState<'registrations' | 'tournaments' | 'users' | 'budgets' | 'broadcast' | 'export'>('registrations')
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
    if (regsFilter) params.set('status', regsFilter)
    if (regsMonthFilter === 'future') params.set('future_only', 'true')
    else if (regsMonthFilter === 'all') params.set('future_only', 'false')
    else params.set('month', regsMonthFilter)
    if (regsSearch.trim()) params.set('search', regsSearch.trim())
    api<AdminRegistration[]>(`/api/v1/admin/registrations?${params}`, { token })
      .then(setRegistrations)
      .catch(() => setRegistrations([]))
      .finally(() => setRegsLoading(false))
  }

  const loadUsers = () => {
    if (!token) return
    setUsersLoading(true)
    const params = new URLSearchParams()
    if (usersSearch.trim()) params.set('search', usersSearch.trim())
    api<AdminUser[]>(`/api/v1/admin/users?${params}`, { token })
      .then(setUsers)
      .catch(() => setUsers([]))
      .finally(() => setUsersLoading(false))
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
    const id = setTimeout(loadRegistrations, regsSearch ? 200 : 0)
    return () => clearTimeout(id)
  }, [token, regsFilter, regsMonthFilter, regsSearch])

  useEffect(() => {
    const id = setTimeout(loadUsers, usersSearch ? 200 : 0)
    return () => clearTimeout(id)
  }, [token, usersSearch])

  useEffect(() => {
    const id = setTimeout(loadTournaments, tournamentsSearch ? 200 : 0)
    return () => clearTimeout(id)
  }, [token, tournamentsMonthFilter, tournamentsSearch])

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
      loadRegistrations()
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
      loadRegistrations()
      setTimeout(() => setResultToast(null), 2500)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Ошибка')
    }
  }

  const handleExportMonth = async () => {
    if (!exportMonth || !token) return
    setExportLoading(true)
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8100'}/api/v1/admin/exports/month?month=${encodeURIComponent(exportMonth)}`,
        { headers: { Authorization: `Bearer ${token}` } }
      )
      if (!res.ok) throw new Error('Ошибка экспорта')
      const blob = await res.blob()
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = `export_${exportMonth}.xlsx`
      a.click()
      URL.revokeObjectURL(a.href)
      showSuccess('Экспорт за месяц скачан')
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Ошибка')
    } finally {
      setExportLoading(false)
    }
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

  const handleExportYear = async () => {
    if (!exportYear || !token) return
    setExportLoading(true)
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8100'}/api/v1/admin/exports/year?year=${encodeURIComponent(exportYear)}`,
        { headers: { Authorization: `Bearer ${token}` } }
      )
      if (!res.ok) throw new Error('Ошибка экспорта')
      const blob = await res.blob()
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = `export_${exportYear}.xlsx`
      a.click()
      URL.revokeObjectURL(a.href)
      showSuccess('Экспорт за год скачан')
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Ошибка')
    } finally {
      setExportLoading(false)
    }
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
          <input
            type="search"
            placeholder="Поиск: имя, фамилия, функция, email..."
            value={usersSearch}
            onChange={(e) => setUsersSearch(e.target.value)}
            className="min-h-[44px] w-full rounded-lg border border-slate-300 px-3 py-2.5 text-slate-800 sm:w-64"
          />
        </div>
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
                          className="flex flex-col gap-3 border-b border-slate-100 px-4 py-3 last:border-b-0 sm:flex-row sm:items-center sm:justify-between"
                        >
                          <div className="pl-8">
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
                            <div className="flex flex-col gap-2 pl-8 sm:flex-row">
                              <button
                                onClick={() => handleApprove(r)}
                                className="inline-flex min-h-[44px] items-center justify-center gap-1 rounded-lg bg-green-600 px-4 py-2.5 text-sm text-white hover:bg-green-700"
                              >
                                <Check className="h-4 w-4" />
                                Одобрить
                              </button>
                              <button
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
