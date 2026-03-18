'use client'

import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { Send, DollarSign, FileSpreadsheet, ClipboardList, Check, X } from 'lucide-react'
import MonthFilter, { type MonthFilterValue } from '@/components/MonthFilter'

type Budget = {
  tournament_id: number
  tournament_name: string
  tournament_date: string
  total_budget: number
  judges_payment: number
  admin_profit: number
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
  const [budgetsMonthFilter, setBudgetsMonthFilter] = useState<MonthFilterValue>('future')

  const [exportMonth, setExportMonth] = useState('')
  const [exportYear, setExportYear] = useState('')
  const [exportLoading, setExportLoading] = useState(false)

  const [resultToast, setResultToast] = useState<{
    type: 'approved' | 'rejected'
    userName: string
    tournamentName: string
  } | null>(null)

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

  useEffect(() => {
    loadBudgets()
  }, [token, budgetsMonthFilter])

  useEffect(() => {
    const id = setTimeout(loadRegistrations, regsSearch ? 350 : 0)
    return () => clearTimeout(id)
  }, [token, regsFilter, regsMonthFilter, regsSearch])

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
    const num = parseFloat(value)
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
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Ошибка')
    } finally {
      setExportLoading(false)
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
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Ошибка')
    } finally {
      setExportLoading(false)
    }
  }

  return (
    <div className="space-y-8">
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
                  <tr key={b.tournament_id} className="border-b border-slate-100">
                    <td className="px-2 py-2">{b.tournament_name}</td>
                    <td className="px-2 py-2 text-slate-600">
                      {typeof b.tournament_date === 'string' ? b.tournament_date : String(b.tournament_date).slice(0, 10)}
                    </td>
                    <td className="px-2 py-2 text-right">{b.total_budget} ₽</td>
                    <td className="px-2 py-2 text-right">{b.judges_payment} ₽</td>
                    <td className="px-2 py-2 text-right">{b.admin_profit} ₽</td>
                    <td className="px-2 py-2">
                      {editingBudget?.id === b.tournament_id ? (
                        <div className="flex gap-1">
                          <input
                            type="number"
                            value={editingBudget.value}
                            onChange={(e) => setEditingBudget({ ...editingBudget, value: e.target.value })}
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
                          onClick={() => setEditingBudget({ id: b.tournament_id, value: String(b.total_budget) })}
                          className="text-xs text-slate-500 hover:text-slate-700"
                        >
                          Изменить
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
            placeholder="Поиск по имени судьи или турниру..."
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
            {registrations.map((r) => (
              <div
                key={r.registration_id}
                className="flex flex-col gap-3 rounded-lg border border-slate-200 p-3 sm:flex-row sm:items-center sm:justify-between"
              >
                <div>
                  <p className="font-medium">{r.tournament_name}</p>
                  <p className="text-sm text-slate-500">
                    {r.user_name} · {r.tournament_date}
                  </p>
                  <span className={`mt-1 inline-block rounded px-2 py-0.5 text-xs ${
                    r.status === 'approved' ? 'bg-green-100 text-green-800' :
                    r.status === 'rejected' ? 'bg-red-100 text-red-800' :
                    'bg-amber-100 text-amber-800'
                  }`}>
                    {r.status === 'pending' ? 'На рассмотрении' : r.status === 'approved' ? 'Одобрена' : 'Отклонена'}
                  </span>
                </div>
                {r.status === 'pending' && (
                  <div className="flex flex-col gap-2 sm:flex-row">
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
            {registrations.length === 0 && (
              <p className="py-4 text-center text-slate-500">Нет заявок</p>
            )}
          </div>
        )}
      </section>

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
    </div>
  )
}
