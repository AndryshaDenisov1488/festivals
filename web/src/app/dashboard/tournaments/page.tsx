'use client'

import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { PlusCircle, Check, XCircle } from 'lucide-react'
import MonthFilter, { type MonthFilterValue } from '@/components/MonthFilter'

type Tournament = {
  tournament_id: number
  name: string
  date: string
  month: string
}

type MyRegistration = {
  tournament_id: number
  registration_id: number
  status: string
}

export default function TournamentsPage() {
  const [items, setItems] = useState<Tournament[]>([])
  const [myRegs, setMyRegs] = useState<Record<number, { status: string; registration_id: number }>>({})
  const [loading, setLoading] = useState(true)
  const [registering, setRegistering] = useState<number | null>(null)
  const [cancelling, setCancelling] = useState<number | null>(null)
  const [monthFilter, setMonthFilter] = useState<MonthFilterValue>('future')
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
        api<Tournament[]>(`/api/v1/tournaments?${params}`, { token }),
        api<MyRegistration[]>(`/api/v1/registrations/my?${params}`, { token })
      ])
        .then(([tours, regs]) => {
          setItems(tours)
          const map: Record<number, { status: string; registration_id: number }> = {}
          regs.forEach((r) => { map[r.tournament_id] = { status: r.status, registration_id: r.registration_id } })
          setMyRegs(map)
        })
        .catch(() => setItems([]))
        .finally(() => setLoading(false))
    }
    const id = search ? setTimeout(load, 200) : null
    if (!id) load()
    return () => { if (id) clearTimeout(id) }
  }, [monthFilter, search])

  const handleRegister = async (tournamentId: number) => {
    const token = localStorage.getItem('token')
    if (!token) return
    setRegistering(tournamentId)
    try {
      const res = await api<{ registration_id: number }>(`/api/v1/registrations`, {
        method: 'POST',
        body: JSON.stringify({ tournament_id: tournamentId }),
        token
      })
      setMyRegs((prev) => ({ ...prev, [tournamentId]: { status: 'pending', registration_id: res.registration_id } }))
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Ошибка подачи заявки')
    } finally {
      setRegistering(null)
    }
  }

  const handleCancel = async (tournamentId: number, registrationId: number) => {
    if (!confirm('Отменить заявку?')) return
    const token = localStorage.getItem('token')
    if (!token) return
    setCancelling(tournamentId)
    try {
      await api(`/api/v1/registrations/${registrationId}`, { method: 'DELETE', token })
      setMyRegs((prev) => {
        const next = { ...prev }
        delete next[tournamentId]
        return next
      })
    } catch {
      alert('Ошибка отмены')
    } finally {
      setCancelling(null)
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
          <h1 className="text-xl font-semibold text-slate-800 md:text-2xl">Турниры</h1>
          <MonthFilter value={monthFilter} onChange={setMonthFilter} />
        </div>
        <input
          type="search"
          placeholder="Поиск: любые буквы подряд..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Поиск турниров"
          className="min-h-[44px] max-w-md rounded-lg border border-slate-300 px-3 py-2.5 text-slate-800 placeholder:text-slate-400 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
        />
      </div>

      {/* Mobile: cards */}
      <div className="space-y-3 md:hidden">
        {items.map((t) => {
          const reg = myRegs[t.tournament_id]
          const status = reg?.status
          const canRegister = !reg
          const isPending = status === 'pending'
          const isApproved = status === 'approved'
          const canCancel = (isPending || isApproved) && reg
          return (
            <div
              key={t.tournament_id}
              className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
            >
              <p className="font-medium text-slate-800">{t.name}</p>
              <p className="text-sm text-slate-500">
                {t.date} · {t.month}
              </p>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                {canRegister && (
                  <button
                    onClick={() => handleRegister(t.tournament_id)}
                    disabled={registering !== null}
                    className="flex min-h-[44px] w-full items-center justify-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-emerald-700 disabled:opacity-50"
                  >
                    <PlusCircle className="h-4 w-4" />
                    {registering === t.tournament_id ? 'Отправка...' : 'Подать заявку'}
                  </button>
                )}
                {isPending && (
                  <span className="inline-flex items-center rounded-full bg-amber-100 px-2.5 py-1 text-xs font-medium text-amber-800">
                    На рассмотрении
                  </span>
                )}
                {isApproved && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-1 text-xs font-medium text-green-800">
                    <Check className="h-3 w-3" />
                    Одобрена
                  </span>
                )}
                {status === 'rejected' && (
                  <span className="inline-flex items-center rounded-full bg-red-100 px-2.5 py-1 text-xs font-medium text-red-800">
                    Отклонена
                  </span>
                )}
                {canCancel && (
                  <button
                    onClick={() => handleCancel(t.tournament_id, reg.registration_id)}
                    disabled={cancelling !== null}
                    className="inline-flex min-h-[44px] items-center gap-1.5 rounded-lg border border-red-200 px-3 py-2 text-sm text-red-600 transition hover:bg-red-50 disabled:opacity-50"
                    aria-label="Отменить заявку"
                  >
                    <XCircle className="h-4 w-4" />
                    {cancelling === t.tournament_id ? 'Отмена...' : 'Отменить'}
                  </button>
                )}
              </div>
            </div>
          )
        })}
        {items.length === 0 && (
          <p className="py-8 text-center text-slate-500">Нет турниров</p>
        )}
      </div>

      {/* Desktop: table */}
      <div className="hidden overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm md:block">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50">
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-600">Название</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-600">Дата</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-600">Месяц</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-slate-600">Действие</th>
            </tr>
          </thead>
          <tbody>
            {items.map((t) => {
              const reg = myRegs[t.tournament_id]
              const status = reg?.status
              const canRegister = !reg
              const isPending = status === 'pending'
              const isApproved = status === 'approved'
              const canCancel = (isPending || isApproved) && reg
              return (
                <tr key={t.tournament_id} className="border-b border-slate-100 last:border-0">
                  <td className="px-4 py-3 text-slate-800">{t.name}</td>
                  <td className="px-4 py-3 text-slate-600">{t.date}</td>
                  <td className="px-4 py-3 text-slate-600">{t.month}</td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex flex-wrap items-center justify-end gap-2">
                      {canRegister && (
                        <button
                          onClick={() => handleRegister(t.tournament_id)}
                          disabled={registering !== null}
                          className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-emerald-700 disabled:opacity-50"
                        >
                          <PlusCircle className="h-4 w-4" />
                          {registering === t.tournament_id ? 'Отправка...' : 'Подать заявку'}
                        </button>
                      )}
                      {isPending && (
                        <span className="inline-flex items-center rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-800">
                          На рассмотрении
                        </span>
                      )}
                      {isApproved && (
                        <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
                          <Check className="h-3 w-3" />
                          Одобрена
                        </span>
                      )}
                      {status === 'rejected' && (
                        <span className="inline-flex items-center rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-800">
                          Отклонена
                        </span>
                      )}
                      {canCancel && (
                        <button
                          onClick={() => handleCancel(t.tournament_id, reg.registration_id)}
                          disabled={cancelling !== null}
                          className="inline-flex items-center gap-1.5 rounded-lg border border-red-200 px-3 py-1.5 text-sm text-red-600 transition hover:bg-red-50 disabled:opacity-50"
                          aria-label="Отменить заявку"
                        >
                          <XCircle className="h-4 w-4" />
                          {cancelling === t.tournament_id ? 'Отмена...' : 'Отменить'}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
        {items.length === 0 && (
          <p className="py-8 text-center text-slate-500">Нет турниров</p>
        )}
      </div>
    </div>
  )
}
