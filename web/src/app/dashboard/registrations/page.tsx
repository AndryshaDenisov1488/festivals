'use client'

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { api } from '@/lib/api'
import MonthFilter, { type MonthFilterValue } from '@/components/MonthFilter'

type Registration = {
  registration_id: number
  tournament_id: number
  status: string
  tournament: { name: string; date: string; month: string }
}

const statusLabels: Record<string, string> = {
  pending: 'На рассмотрении',
  approved: 'Одобрена',
  rejected: 'Отклонена'
}

export default function RegistrationsPage() {
  const searchParams = useSearchParams()
  const statusFromUrl = searchParams.get('status') as 'pending' | 'approved' | 'rejected' | null
  const [items, setItems] = useState<Registration[]>([])
  const [loading, setLoading] = useState(true)
  const [monthFilter, setMonthFilter] = useState<MonthFilterValue>('future')
  const [statusFilter, setStatusFilter] = useState<'pending' | 'approved' | 'rejected' | ''>(
    statusFromUrl && ['pending', 'approved', 'rejected'].includes(statusFromUrl) ? statusFromUrl : ''
  )
  const [search, setSearch] = useState('')

  useEffect(() => {
    if (statusFromUrl && ['pending', 'approved', 'rejected'].includes(statusFromUrl)) {
      setStatusFilter(statusFromUrl)
      if (statusFromUrl === 'rejected') setMonthFilter('all')
    }
  }, [statusFromUrl])

  useEffect(() => {
    if (statusFilter === 'rejected') setMonthFilter('all')
  }, [statusFilter])

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) return
    const load = () => {
      const params = new URLSearchParams()
      if (monthFilter === 'future') params.set('future_only', 'true')
      else if (monthFilter === 'all') params.set('future_only', 'false')
      else params.set('month', monthFilter)
      if (statusFilter) params.set('status', statusFilter)
      if (search.trim()) params.set('search', search.trim())
      setLoading(true)
      api<Registration[]>(`/api/v1/registrations/my?${params}`, { token })
        .then(setItems)
        .catch(() => setItems([]))
        .finally(() => setLoading(false))
    }
    const id = search ? setTimeout(load, 200) : null
    if (!id) load()
    return () => { if (id) clearTimeout(id) }
  }, [monthFilter, statusFilter, search])

  const handleCancel = async (id: number) => {
    if (!confirm('Отменить заявку?')) return
    const token = localStorage.getItem('token')
    if (!token) return
    try {
      await api(`/api/v1/registrations/${id}`, { method: 'DELETE', token })
      setItems((prev) => prev.filter((r) => r.registration_id !== id))
    } catch {
      alert('Ошибка отмены')
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
      </div>
    )
  }

  return (
    <div>
      <div className="mb-4 flex flex-col gap-4 md:mb-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h1 className="text-xl font-semibold text-slate-800 md:text-2xl">Мои заявки</h1>
          <MonthFilter value={monthFilter} onChange={setMonthFilter} />
        </div>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <input
            type="search"
            placeholder="Поиск: любые буквы подряд..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="Поиск заявок"
            className="min-h-[44px] flex-1 rounded-lg border border-slate-300 px-3 py-2.5 text-slate-800 placeholder:text-slate-400 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500 sm:max-w-xs"
          />
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setStatusFilter('')}
              className={`min-h-[44px] rounded-lg px-4 py-2.5 text-sm ${!statusFilter ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-600'}`}
            >
              Все
            </button>
            <button
              onClick={() => setStatusFilter('pending')}
              className={`min-h-[44px] rounded-lg px-4 py-2.5 text-sm ${statusFilter === 'pending' ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-600'}`}
            >
              На рассмотрении
            </button>
            <button
              onClick={() => setStatusFilter('approved')}
              className={`min-h-[44px] rounded-lg px-4 py-2.5 text-sm ${statusFilter === 'approved' ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-600'}`}
            >
              Одобренные
            </button>
            <button
              onClick={() => setStatusFilter('rejected')}
              className={`min-h-[44px] rounded-lg px-4 py-2.5 text-sm ${statusFilter === 'rejected' ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-600'}`}
            >
              Отклонённые
            </button>
          </div>
        </div>
      </div>
      <div className="space-y-3">
        {items.map((r) => (
          <div
            key={r.registration_id}
            className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:flex-row sm:items-center sm:justify-between"
          >
            <div>
              <p className="font-medium text-slate-800">{r.tournament.name}</p>
              <p className="text-sm text-slate-500">
                {r.tournament.date} · {r.tournament.month}
              </p>
              <span
                className={`mt-1 inline-block rounded px-2 py-0.5 text-xs font-medium ${
                  r.status === 'approved'
                    ? 'bg-green-100 text-green-800'
                    : r.status === 'rejected'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-amber-100 text-amber-800'
                }`}
              >
                {statusLabels[r.status] ?? r.status}
              </span>
            </div>
            {r.status === 'pending' && (
              <button
                onClick={() => handleCancel(r.registration_id)}
                className="min-h-[44px] rounded-lg border border-red-200 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50"
              >
                Отменить
              </button>
            )}
          </div>
        ))}
        {items.length === 0 && (
          <p className="py-8 text-center text-slate-500">Нет заявок</p>
        )}
      </div>
    </div>
  )
}
