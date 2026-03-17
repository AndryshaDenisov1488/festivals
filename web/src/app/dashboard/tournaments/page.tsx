'use client'

import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { PlusCircle, Check } from 'lucide-react'

type Tournament = {
  tournament_id: number
  name: string
  date: string
  month: string
}

type MyRegistration = {
  tournament_id: number
  status: string
}

export default function TournamentsPage() {
  const [items, setItems] = useState<Tournament[]>([])
  const [myRegs, setMyRegs] = useState<Record<number, string>>({})
  const [loading, setLoading] = useState(true)
  const [registering, setRegistering] = useState<number | null>(null)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) return
    Promise.all([
      api<Tournament[]>('/api/v1/tournaments', { token }),
      api<MyRegistration[]>('/api/v1/registrations/my', { token })
    ])
      .then(([tours, regs]) => {
        setItems(tours)
        const map: Record<number, string> = {}
        regs.forEach((r) => { map[r.tournament_id] = r.status })
        setMyRegs(map)
      })
      .catch(() => setItems([]))
      .finally(() => setLoading(false))
  }, [])

  const handleRegister = async (tournamentId: number) => {
    const token = localStorage.getItem('token')
    if (!token) return
    setRegistering(tournamentId)
    try {
      await api(`/api/v1/registrations`, {
        method: 'POST',
        body: JSON.stringify({ tournament_id: tournamentId }),
        token
      })
      setMyRegs((prev) => ({ ...prev, [tournamentId]: 'pending' }))
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Ошибка подачи заявки')
    } finally {
      setRegistering(null)
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
      <h1 className="mb-6 text-2xl font-semibold text-slate-800">Турниры</h1>
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
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
              const status = myRegs[t.tournament_id]
              const canRegister = !status
              const isPending = status === 'pending'
              const isApproved = status === 'approved'
              return (
                <tr key={t.tournament_id} className="border-b border-slate-100 last:border-0">
                  <td className="px-4 py-3 text-slate-800">{t.name}</td>
                  <td className="px-4 py-3 text-slate-600">{t.date}</td>
                  <td className="px-4 py-3 text-slate-600">{t.month}</td>
                  <td className="px-4 py-3 text-right">
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
