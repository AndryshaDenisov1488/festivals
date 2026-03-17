'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'

export default function LoginPage() {
  const router = useRouter()
  const [step, setStep] = useState<'email' | 'code'>('email')
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleRequestCode = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await api('/api/v1/auth/request-code', {
        method: 'POST',
        body: JSON.stringify({ email })
      })
      setStep('code')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка запроса кода')
    } finally {
      setLoading(false)
    }
  }

  const handleVerifyCode = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await api<{ access_token: string }>('/api/v1/auth/verify-code', {
        method: 'POST',
        body: JSON.stringify({ email, code })
      })
      if (res?.access_token) {
        localStorage.setItem('token', res.access_token)
        router.replace('/dashboard')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Неверный код')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 p-4">
      <div className="w-full max-w-sm rounded-xl bg-white p-6 shadow-lg">
        <h1 className="mb-6 text-center text-xl font-semibold text-slate-800">
          Вход в кабинет судьи
        </h1>

        {step === 'email' ? (
          <form onSubmit={handleRequestCode} className="space-y-4">
            <div>
              <label htmlFor="email" className="mb-1 block text-sm font-medium text-slate-600">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-800 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
                placeholder="judge@example.com"
                disabled={loading}
              />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-slate-800 py-2 font-medium text-white transition hover:bg-slate-700 disabled:opacity-50"
            >
              {loading ? 'Отправка...' : 'Получить код'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerifyCode} className="space-y-4">
            <p className="text-sm text-slate-600">
              Код отправлен на <strong>{email}</strong>
            </p>
            <div>
              <label htmlFor="code" className="mb-1 block text-sm font-medium text-slate-600">
                Код из письма
              </label>
              <input
                id="code"
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                required
                maxLength={6}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-center text-lg tracking-widest text-slate-800 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
                placeholder="000000"
                disabled={loading}
              />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-slate-800 py-2 font-medium text-white transition hover:bg-slate-700 disabled:opacity-50"
            >
              {loading ? 'Проверка...' : 'Войти'}
            </button>
            <button
              type="button"
              onClick={() => setStep('email')}
              className="w-full text-sm text-slate-500 hover:text-slate-700"
            >
              Изменить email
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
