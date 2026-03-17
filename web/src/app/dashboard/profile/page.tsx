'use client'

import { useEffect, useState } from 'react'
import { api } from '@/lib/api'

type User = {
  user_id: number
  first_name?: string
  last_name?: string
  function?: string
  category?: string
  email?: string
  is_admin?: boolean
}

export default function ProfilePage() {
  const [user, setUser] = useState<User | null>(null)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) return
    api<User>('/api/v1/users/me', { token })
      .then(setUser)
      .catch(() => setUser(null))
  }, [])

  if (!user) {
    return (
      <div className="flex justify-center py-12">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
      </div>
    )
  }

  return (
    <div>
      <h1 className="mb-6 text-2xl font-semibold text-slate-800">Профиль</h1>
      <div className="max-w-md space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div>
          <p className="text-sm text-slate-500">Имя</p>
          <p className="font-medium text-slate-800">
            {[user.first_name, user.last_name].filter(Boolean).join(' ') || '—'}
          </p>
        </div>
        {(user.function || user.category) && (
          <div>
            <p className="text-sm text-slate-500">Функция / Категория</p>
            <p className="font-medium text-slate-800">
              {[user.function, user.category].filter(Boolean).join(' · ') || '—'}
            </p>
          </div>
        )}
        <div>
          <p className="text-sm text-slate-500">Email</p>
          <p className="font-medium text-slate-800">{user.email || '—'}</p>
        </div>
        {user.is_admin && (
          <p className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">Администратор</p>
        )}
      </div>
    </div>
  )
}
