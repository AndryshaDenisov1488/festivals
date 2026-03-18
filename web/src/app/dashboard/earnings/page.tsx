'use client'

import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { Check, Edit2, Trophy } from 'lucide-react'
import MonthFilter, { type MonthFilterValue } from '@/components/MonthFilter'

type Payment = {
  payment_id: number
  tournament_id: number
  tournament_name: string
  tournament_date: string
  tournament_month?: string
  amount: number | null
  is_paid: boolean
  payment_date: string | null
}

type ProgressToNext = { current: number; target: number; next_label: string }
type SummaryResponse = {
  total_amount?: number
  total_tournaments?: number
  rating?: string
  progress_to_next?: ProgressToNext | null
}

export default function EarningsPage() {
  const [payments, setPayments] = useState<Payment[]>([])
  const [summary, setSummary] = useState<SummaryResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [confirming, setConfirming] = useState<number | null>(null)
  const [correcting, setCorrecting] = useState<number | null>(null)
  const [confirmAmount, setConfirmAmount] = useState('')
  const [correctAmount, setCorrectAmount] = useState('')
  const [modalPayment, setModalPayment] = useState<Payment | null>(null)
  const [monthFilter, setMonthFilter] = useState<MonthFilterValue>('all')
  const [search, setSearch] = useState('')

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) return
    const load = () => {
      const params = new URLSearchParams()
      if (monthFilter === 'future') params.set('future_only', 'true')
      else if (monthFilter === 'all') params.set('future_only', 'false')
      else params.set('month', monthFilter)
      if (search.trim()) params.set('search', search.trim())
      setLoading(true)
      Promise.all([
        api<Payment[]>(`/api/v1/earnings/my/payments?${params}`, { token: token ?? undefined }),
        api<SummaryResponse>('/api/v1/earnings/my/summary', { token: token ?? undefined })
      ])
        .then(([p, s]) => {
          setPayments(p ?? [])
          setSummary(s ?? null)
        })
        .catch(() => setPayments([]))
        .finally(() => setLoading(false))
    }
    const id = search ? setTimeout(load, 200) : null
    if (!id) load()
    return () => { if (id) clearTimeout(id) }
  }, [monthFilter, search])

  const handleConfirm = async (payment: Payment) => {
    const amount = parseFloat(confirmAmount)
    if (isNaN(amount) || amount < 3500) {
      alert('Минимальная сумма 3500 ₽')
      return
    }
    const token = localStorage.getItem('token')
    if (!token) return
    setConfirming(payment.payment_id)
    try {
      await api(`/api/v1/earnings/my/confirm`, {
        method: 'POST',
        body: JSON.stringify({ payment_id: payment.payment_id, amount }),
        token: token ?? undefined
      })
      const paymentDate = new Date().toLocaleString('ru-RU', {
        timeZone: 'Europe/Moscow',
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
      setPayments((prev) =>
        prev.map((p) =>
          p.payment_id === payment.payment_id
            ? { ...p, is_paid: true, amount, payment_date: paymentDate }
            : p
        )
      )
      const refreshToken = localStorage.getItem('token')
      if (refreshToken) {
        api<SummaryResponse>('/api/v1/earnings/my/summary', { token: refreshToken ?? undefined }).then(setSummary).catch(() => {})
      }
      setModalPayment(null)
      setConfirmAmount('')
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Ошибка')
    } finally {
      setConfirming(null)
    }
  }

  const handleCorrect = async (payment: Payment) => {
    const amount = parseFloat(correctAmount)
    if (isNaN(amount) || amount <= 0) {
      alert('Введите корректную сумму')
      return
    }
    const token = localStorage.getItem('token')
    if (!token) return
    setCorrecting(payment.payment_id)
    try {
      await api(`/api/v1/earnings/my/correct`, {
        method: 'POST',
        body: JSON.stringify({ payment_id: payment.payment_id, amount }),
        token: token ?? undefined
      })
      setPayments((prev) =>
        prev.map((p) =>
          p.payment_id === payment.payment_id ? { ...p, amount } : p
        )
      )
      setModalPayment(null)
      setCorrectAmount('')
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Ошибка')
    } finally {
      setCorrecting(null)
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
      </div>
    )
  }

  const paidPayments = payments.filter((p) => p.is_paid)
  const unpaidPayments = payments.filter((p) => !p.is_paid)

  return (
    <div>
      <div className="mb-4 flex flex-col gap-4 md:mb-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h1 className="text-xl font-semibold text-slate-800 md:text-2xl">Выплаты</h1>
          <MonthFilter value={monthFilter} onChange={setMonthFilter} />
        </div>
        <input
          type="search"
          placeholder="Поиск: любые буквы подряд..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Поиск выплат"
          className="min-h-[44px] max-w-md rounded-lg border border-slate-300 px-3 py-2.5 text-slate-800 placeholder:text-slate-400 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
        />
      </div>
      {/* Summary + Achievements */}
      {summary && (
        <div className="mb-6 space-y-4">
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <p className="text-sm text-slate-500">Итого</p>
            <p className="text-2xl font-semibold text-slate-800">{summary.total_amount ?? 0} ₽</p>
            {summary.total_tournaments != null && (
              <p className="mt-1 text-sm text-slate-600">за {summary.total_tournaments} турниров</p>
            )}
          </div>
          {(summary.rating || summary.progress_to_next) && (
            <div className="rounded-xl border border-amber-200 bg-amber-50/30 p-4 shadow-sm">
              <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-amber-800">
                <Trophy className="h-4 w-4" />
                Достижения
              </h2>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                {summary.rating && (
                  <span className="font-semibold text-amber-800">{summary.rating}</span>
                )}
                {summary.progress_to_next && (
                  <div className="min-w-[200px]">
                    <p className="mb-1 text-xs text-slate-600">
                      До {summary.progress_to_next.next_label}
                    </p>
                    <div className="flex items-center gap-2">
                      <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-slate-200">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-amber-400 to-amber-600"
                          style={{ width: `${Math.min(100, (summary.progress_to_next.current / summary.progress_to_next.target) * 100)}%` }}
                        />
                      </div>
                      <span className="text-sm font-mono font-medium text-slate-700">
                        {summary.progress_to_next.current}/{summary.progress_to_next.target}
                      </span>
                    </div>
                  </div>
                )}
                {!summary.progress_to_next && summary.rating && (
                  <p className="text-sm text-amber-700">Максимальный статус достигнут</p>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {unpaidPayments.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-3 text-lg font-medium text-slate-700">Ожидают подтверждения</h2>
          <div className="space-y-3">
            {unpaidPayments.map((p) => (
              <div
                key={p.payment_id}
                className="flex items-center justify-between rounded-xl border border-amber-200 bg-amber-50/50 p-4"
              >
                <div>
                  <p className="font-medium text-slate-800">{p.tournament_name}</p>
                  <p className="text-sm text-slate-500">{p.tournament_date}</p>
                </div>
                <button
                  onClick={() => setModalPayment({ ...p, amount: null })}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700"
                >
                  <Check className="h-4 w-4" />
                  Подтвердить получение
                </button>
              </div>
            ))}
          </div>
        </section>
      )}

      <section>
        <h2 className="mb-3 text-lg font-medium text-slate-700">История выплат</h2>
        <div className="space-y-3">
          {paidPayments.map((p) => (
            <div
              key={p.payment_id}
              className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
            >
              <div>
                <p className="font-medium text-slate-800">{p.tournament_name}</p>
                <p className="text-sm text-slate-500">
                  {p.tournament_date}
                  {p.payment_date ? ` · Оплачено: ${p.payment_date}` : ''}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <p className="font-semibold text-slate-800">{p.amount ?? 0} ₽</p>
                <button
                  onClick={() => {
                    setModalPayment(p)
                    setCorrectAmount(String(p.amount ?? ''))
                  }}
                  className="rounded-lg border border-slate-300 p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-700"
                  title="Исправить сумму"
                >
                  <Edit2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
        {payments.length === 0 && (
          <p className="py-8 text-center text-slate-500">Нет выплат</p>
        )}
      </section>

      {modalPayment && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          onClick={() => setModalPayment(null)}
        >
          <div
            className="w-full max-w-sm rounded-xl bg-white p-6 shadow-xl mx-4 max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="mb-4 font-semibold text-slate-800">
              {modalPayment.tournament_name}
            </h3>
            {!modalPayment.is_paid ? (
              <>
                <label className="mb-2 block text-sm text-slate-600">
                  Сумма полученной оплаты (мин. 3500 ₽)
                </label>
                <input
                  type="number"
                  value={confirmAmount}
                  onChange={(e) => setConfirmAmount(e.target.value)}
                  placeholder="3500"
                  min={3500}
                  className="mb-4 w-full rounded-lg border border-slate-300 px-3 py-2"
                />
                <div className="flex gap-2">
                  <button
                    onClick={() => handleConfirm(modalPayment)}
                    disabled={confirming !== null}
                    className="min-h-[44px] flex-1 rounded-lg bg-emerald-600 py-2.5 text-white hover:bg-emerald-700 disabled:opacity-50"
                  >
                    {confirming ? 'Сохранение...' : 'Подтвердить'}
                  </button>
                  <button
                    onClick={() => setModalPayment(null)}
                    className="min-h-[44px] rounded-lg border border-slate-300 px-4 py-2.5 hover:bg-slate-50"
                  >
                    Отмена
                  </button>
                </div>
              </>
            ) : (
              <>
                <label className="mb-2 block text-sm text-slate-600">
                  Исправить сумму
                </label>
                <input
                  type="number"
                  value={correctAmount}
                  onChange={(e) => setCorrectAmount(e.target.value)}
                  min={1}
                  className="mb-4 w-full rounded-lg border border-slate-300 px-3 py-2"
                />
                <div className="flex gap-2">
                  <button
                    onClick={() => handleCorrect(modalPayment)}
                    disabled={correcting !== null}
                    className="min-h-[44px] flex-1 rounded-lg bg-slate-800 py-2.5 text-white hover:bg-slate-700 disabled:opacity-50"
                  >
                    {correcting ? 'Сохранение...' : 'Сохранить'}
                  </button>
                  <button
                    onClick={() => setModalPayment(null)}
                    className="min-h-[44px] rounded-lg border border-slate-300 px-4 py-2.5 hover:bg-slate-50"
                  >
                    Отмена
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
