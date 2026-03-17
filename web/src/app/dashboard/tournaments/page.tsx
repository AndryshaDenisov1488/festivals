'use client'

import { useEffect, useState } from 'react'
import { api } from '@/lib/api'

type Tournament = {
  tournament_id: number
  name: string
  date: string
  month: string
}

export default function TournamentsPage() {
  const [items, setItems] = useState<Tournament[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) return
    api<Tournament[]>('/api/v1/tournaments', { token })
      .then(setItems)
      .catch(() => setItems([]))
      .finally(() => setLoading(false))
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
      <h1 className="mb-6 text-2xl font-semibold text-slate-800">Турниры</h1>
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50">
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-600">Название</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-600">Дата</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-600">Месяц</th>
            </tr>
          </thead>
          <tbody>
            {items.map((t) => (
              <tr key={t.tournament_id} className="border-b border-slate-100 last:border-0">
                <td className="px-4 py-3 text-slate-800">{t.name}</td>
                <td className="px-4 py-3 text-slate-600">{t.date}</td>
                <td className="px-4 py-3 text-slate-600">{t.month}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && (
          <p className="py-8 text-center text-slate-500">Нет турниров</p>
        )}
      </div>
    </div>
  )
}
