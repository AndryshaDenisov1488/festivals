'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'

type LoginMode = 'code' | 'password'

export default function LoginPage() {
  const router = useRouter()
  const [mode, setMode] = useState<LoginMode>('password')
  const [step, setStep] = useState<'email' | 'code'>('email')
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')
  const [password, setPassword] = useState('')
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

  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await api<{ access_token: string }>('/api/v1/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
      })
      if (res?.access_token) {
        localStorage.setItem('token', res.access_token)
        router.replace('/dashboard')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Неверный email или пароль')
    } finally {
      setLoading(false)
    }
  }

  const handleModeChange = (newMode: LoginMode) => {
    setMode(newMode)
    setStep('email')
    setError('')
    setCode('')
    setPassword('')
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-100 via-white to-slate-50 p-4">
      <div className="w-full max-w-sm rounded-2xl border border-slate-200/60 bg-white/90 p-8 shadow-xl backdrop-blur">
        <h1 className="mb-2 text-center text-2xl font-bold tracking-tight text-slate-800">
          Вход
        </h1>
        <p className="mb-6 text-center text-sm text-slate-500">
          Войдите для доступа к Фестивальчикам для судей
        </p>

        <div className="mb-4 flex rounded-lg bg-slate-100 p-1">
          <button
            type="button"
            onClick={() => handleModeChange('password')}
            className={`flex-1 rounded-md py-2 text-sm font-medium transition ${
              mode === 'password' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-600 hover:text-slate-800'
            }`}
          >
            По паролю
          </button>
          <button
            type="button"
            onClick={() => handleModeChange('code')}
            className={`flex-1 rounded-md py-2 text-sm font-medium transition ${
              mode === 'code' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-600 hover:text-slate-800'
            }`}
          >
            По коду
          </button>
        </div>

        {mode === 'password' ? (
          <form onSubmit={handlePasswordLogin} className="space-y-4">
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
                className="w-full rounded-xl border border-slate-200 px-4 py-3 text-slate-800 transition focus:border-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-400/30"
                placeholder="judge@example.com"
                disabled={loading}
                autoComplete="email"
              />
            </div>
            <div>
              <label htmlFor="password" className="mb-1 block text-sm font-medium text-slate-600">
                Пароль
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full rounded-xl border border-slate-200 px-4 py-3 text-slate-800 transition focus:border-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-400/30"
                placeholder="••••••••"
                disabled={loading}
                autoComplete="current-password"
              />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="min-h-[48px] w-full rounded-xl bg-slate-800 py-3 font-semibold text-white shadow-sm transition hover:bg-slate-700 hover:shadow disabled:opacity-50"
            >
              {loading ? 'Вход...' : 'Войти'}
            </button>
          </form>
        ) : step === 'email' ? (
          <form onSubmit={handleRequestCode} className="space-y-4">
            <div>
              <label htmlFor="email-code" className="mb-1 block text-sm font-medium text-slate-600">
                Email
              </label>
              <input
                id="email-code"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full rounded-xl border border-slate-200 px-4 py-3 text-slate-800 transition focus:border-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-400/30"
                placeholder="judge@example.com"
                disabled={loading}
                autoComplete="email"
              />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="min-h-[48px] w-full rounded-xl bg-slate-800 py-3 font-semibold text-white shadow-sm transition hover:bg-slate-700 hover:shadow disabled:opacity-50"
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
                className="w-full rounded-xl border border-slate-200 px-4 py-3 text-center text-lg tracking-widest text-slate-800 transition focus:border-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-400/30"
                placeholder="000000"
                disabled={loading}
              />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="min-h-[48px] w-full rounded-xl bg-slate-800 py-3 font-semibold text-white shadow-sm transition hover:bg-slate-700 hover:shadow disabled:opacity-50"
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

        <p className="mt-4 text-center text-xs text-slate-500">
          <Link href="/" className="text-slate-600 hover:underline">
            ← На главную
          </Link>
        </p>
      </div>
    </div>
  )
}
