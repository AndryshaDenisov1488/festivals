'use client'

import { useEffect, useState } from 'react'
import { api } from '@/lib/api'

type TournamentEarning = {
  name: string
  date: string | null
  amount: number
  payment_date: string | null
}

type DetailResponse = {
  tournament_earnings?: TournamentEarning[]
  total_amount?: number
}

type SummaryResponse = { total_amount?: number }

export default function EarningsPage() {
  const [detail, setDetail] = useState<TournamentEarning[]>([])
  const [summary, setSummary] = useState<SummaryResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) return
    Promise.all([
      api<DetailResponse>('/api/v1/earnings/my/detail', { token }).catch(() => ({})),
      api<SummaryResponse>('/api/v1/earnings/my/summary', { token }).catch(() => null)
    ]).then(([d, s]) => {
      const resp = d as DetailResponse | Record<string, never>
      setDetail('tournament_earnings' in resp ? (resp.tournament_earnings ?? []) : [])
      setSummary(s)
    }).finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
      </div>
    )
  }

  return (
    <div>
      <h1 className="mb-6 text-2xl font-semibold text-slate-800">Выплаты</h1>
      {summary?.total_amount != null && (
        <div className="mb-6 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-sm text-slate-500">Итого</p>
          <p className="text-2xl font-semibold text-slate-800">{summary.total_amount} ₽</p>
        </div>
      )}
      <div className="space-y-3">
        {detail.map((e, i) => (
          <div
            key={i}
            className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
          >
            <div>
              <p className="font-medium text-slate-800">{e.name}</p>
              <p className="text-sm text-slate-500">
                {e.date ?? '—'} {e.payment_date ? `· Оплачено: ${e.payment_date}` : ''}
              </p>
            </div>
            <p className="font-semibold text-slate-800">{e.amount} ₽</p>
          </div>
        ))}
        {detail.length === 0 && (
          <p className="py-8 text-center text-slate-500">Нет выплат</p>
        )}
      </div>
    </div>
  )
}
