'use client'

import { useState } from 'react'
import { api } from '@/lib/api'

export default function AdminPage() {
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<{ total?: number; ok?: number; fail?: number } | null>(null)

  const handleBroadcast = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!message.trim()) return
    setLoading(true)
    setResult(null)
    try {
      const res = await api<{ total: number; ok: number; fail: number }>(
        '/api/v1/admin/broadcast',
        {
          method: 'POST',
          body: JSON.stringify({ message: message.trim() }),
          token: localStorage.getItem('token') ?? undefined
        }
      )
      setResult(res)
    } catch (err) {
      setResult({ total: 0, ok: 0, fail: 0 })
      alert(err instanceof Error ? err.message : 'Ошибка')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 className="mb-6 text-2xl font-semibold text-slate-800">Админ-панель</h1>
      <div className="max-w-lg space-y-6">
        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 font-medium text-slate-800">Рассылка</h2>
          <form onSubmit={handleBroadcast} className="space-y-4">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Сообщение для всех судей..."
              rows={4}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-800 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-slate-800 px-4 py-2 font-medium text-white transition hover:bg-slate-700 disabled:opacity-50"
            >
              {loading ? 'Отправка...' : 'Отправить в Telegram'}
            </button>
          </form>
          {result && (
            <p className="mt-4 text-sm text-slate-600">
              Отправлено: {result.ok} из {result.total}, ошибок: {result.fail}
            </p>
          )}
        </section>
        <p className="text-sm text-slate-500">
          Бюджеты и экспорты доступны через API. Полный функционал — в Telegram-боте.
        </p>
      </div>
    </div>
  )
}
