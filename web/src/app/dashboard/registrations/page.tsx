'use client'

import { useEffect, useState } from 'react'
import { api } from '@/lib/api'

type Registration = {
  registration_id: number
  tournament_id: number
  status: string
  tournament: { name: string; date: string; month: string }
}

const statusLabels: Record<string, string> = {
  PENDING: 'На рассмотрении',
  APPROVED: 'Одобрена',
  REJECTED: 'Отклонена'
}

export default function RegistrationsPage() {
  const [items, setItems] = useState<Registration[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) return
    api<Registration[]>('/api/v1/registrations/my', { token })
      .then(setItems)
      .catch(() => setItems([]))
      .finally(() => setLoading(false))
  }, [])

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
      <h1 className="mb-6 text-2xl font-semibold text-slate-800">Мои заявки</h1>
      <div className="space-y-3">
        {items.map((r) => (
          <div
            key={r.registration_id}
            className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
          >
            <div>
              <p className="font-medium text-slate-800">{r.tournament.name}</p>
              <p className="text-sm text-slate-500">
                {r.tournament.date} · {r.tournament.month}
              </p>
              <span
                className={`mt-1 inline-block rounded px-2 py-0.5 text-xs font-medium ${
                  r.status === 'APPROVED'
                    ? 'bg-green-100 text-green-800'
                    : r.status === 'REJECTED'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-amber-100 text-amber-800'
                }`}
              >
                {statusLabels[r.status] ?? r.status}
              </span>
            </div>
            {r.status === 'PENDING' && (
              <button
                onClick={() => handleCancel(r.registration_id)}
                className="rounded-lg border border-red-200 px-3 py-1 text-sm text-red-600 hover:bg-red-50"
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
