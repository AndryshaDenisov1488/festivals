'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import {
  LayoutDashboard,
  Trophy,
  ClipboardList,
  Wallet,
  User,
  Settings,
  LogOut,
  Menu,
  X
} from 'lucide-react'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'

type UserInfo = {
  user_id: number
  first_name?: string
  last_name?: string
  email?: string
  is_admin?: boolean
  has_password?: boolean
}

function SetPasswordModal({
  onSuccess
}: {
  onSuccess: () => void
}) {
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (password.length < 8) {
      setError('Пароль должен быть не менее 8 символов')
      return
    }
    if (password !== confirm) {
      setError('Пароли не совпадают')
      return
    }
    const token = localStorage.getItem('token')
    if (!token) return
    setLoading(true)
    try {
      await api('/api/v1/auth/set-password', {
        method: 'POST',
        body: JSON.stringify({ password }),
        token
      })
      onSuccess()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка сохранения')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div
        className="w-full max-w-sm rounded-xl bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="mb-2 text-lg font-semibold text-slate-800">Задайте пароль</h3>
        <p className="mb-4 text-sm text-slate-500">
          Для входа по email и паролю задайте пароль. Он будет использоваться при следующем входе.
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="set-password" className="mb-1 block text-sm font-medium text-slate-600">
              Пароль
            </label>
            <input
              id="set-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-slate-800 focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-400/30"
              placeholder="Минимум 8 символов"
              disabled={loading}
              autoComplete="new-password"
            />
          </div>
          <div>
            <label htmlFor="set-password-confirm" className="mb-1 block text-sm font-medium text-slate-600">
              Повторите пароль
            </label>
            <input
              id="set-password-confirm"
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              required
              minLength={8}
              className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-slate-800 focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-400/30"
              placeholder="Повторите пароль"
              disabled={loading}
              autoComplete="new-password"
            />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-slate-800 py-2.5 font-medium text-white hover:bg-slate-700 disabled:opacity-50"
          >
            {loading ? 'Сохранение...' : 'Сохранить'}
          </button>
        </form>
      </div>
    </div>
  )
}

const navItems = [
  { href: '/dashboard', label: 'Обзор', icon: LayoutDashboard },
  { href: '/dashboard/tournaments', label: 'Турниры', icon: Trophy },
  { href: '/dashboard/registrations', label: 'Заявки', icon: ClipboardList },
  { href: '/dashboard/earnings', label: 'Выплаты', icon: Wallet },
  { href: '/dashboard/profile', label: 'Профиль', icon: User }
]

export default function DashboardLayout({
  children
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()
  const router = useRouter()
  const [user, setUser] = useState<UserInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [showSetPassword, setShowSetPassword] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      router.replace('/login')
      return
    }
    api<UserInfo>('/api/v1/users/me', { token })
      .then((u) => {
        setUser(u)
        if (u && u.has_password === false) {
          setShowSetPassword(true)
        }
      })
      .catch(() => {
        localStorage.removeItem('token')
        router.replace('/login')
      })
      .finally(() => setLoading(false))
  }, [router])

  const handleSetPasswordSuccess = () => {
    setShowSetPassword(false)
    setUser((prev) => (prev ? { ...prev, has_password: true } : prev))
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    router.replace('/login')
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
      </div>
    )
  }

  const NavContent = () => (
    <>
      {navItems.map(({ href, label, icon: Icon }) => (
        <Link
          key={href}
          href={href}
          onClick={() => setMobileMenuOpen(false)}
          className={cn(
            'flex min-h-[44px] items-center gap-2 rounded-lg px-3 py-2.5 text-sm transition',
            pathname === href
              ? 'bg-slate-100 font-medium text-slate-900'
              : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
          )}
        >
          <Icon className="h-5 w-5 shrink-0" />
          {label}
        </Link>
      ))}
      {user?.is_admin && (
        <Link
          href="/dashboard/admin"
          onClick={() => setMobileMenuOpen(false)}
          className={cn(
            'flex min-h-[44px] items-center gap-2 rounded-lg px-3 py-2.5 text-sm transition',
            pathname === '/dashboard/admin'
              ? 'bg-slate-100 font-medium text-slate-900'
              : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
          )}
        >
          <Settings className="h-5 w-5 shrink-0" />
          Админ
        </Link>
      )}
      <div className="mt-auto border-t border-slate-200 pt-2">
        <button
          onClick={() => {
            setMobileMenuOpen(false)
            handleLogout()
          }}
          className="flex min-h-[44px] w-full items-center gap-2 rounded-lg px-3 py-2.5 text-sm text-slate-600 transition hover:bg-slate-50 hover:text-slate-900"
        >
          <LogOut className="h-5 w-5 shrink-0" />
          Выйти
        </button>
      </div>
    </>
  )

  return (
    <div className="flex min-h-screen">
      {showSetPassword && (
        <SetPasswordModal onSuccess={handleSetPasswordSuccess} />
      )}

      {/* Mobile overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={() => setMobileMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Mobile drawer */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-slate-200 bg-white shadow-xl transition-transform duration-200 ease-out md:hidden',
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex h-14 items-center justify-between border-b border-slate-200 px-4">
          <span className="font-bold tracking-tight text-slate-800">Меню</span>
          <button
            onClick={() => setMobileMenuOpen(false)}
            className="flex min-h-[44px] min-w-[44px] items-center justify-center rounded-lg text-slate-600 hover:bg-slate-100"
            aria-label="Закрыть меню"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <nav className="flex flex-1 flex-col space-y-1 overflow-auto p-2">
          <NavContent />
        </nav>
      </aside>

      {/* Desktop sidebar */}
      <aside className="hidden w-56 flex-col border-r border-slate-200 bg-white shadow-sm md:flex">
        <div className="flex h-16 items-center border-b border-slate-200 px-4">
          <span className="text-lg font-bold tracking-tight text-slate-800">Кабинет судьи</span>
        </div>
        <nav className="flex flex-1 flex-col space-y-1 p-2">
          <NavContent />
        </nav>
      </aside>

      <div className="flex flex-1 flex-col min-h-screen">
        {/* Mobile header */}
        <header className="flex h-14 items-center justify-between border-b border-slate-200 bg-white px-4 md:hidden">
          <button
            onClick={() => setMobileMenuOpen(true)}
            className="flex min-h-[44px] min-w-[44px] items-center justify-center rounded-lg text-slate-600 hover:bg-slate-100"
            aria-label="Открыть меню"
          >
            <Menu className="h-6 w-6" />
          </button>
          <span className="font-bold tracking-tight text-slate-800">Кабинет судьи</span>
          <div className="w-11" />
        </header>

        <main className="flex-1 overflow-auto p-4 md:p-6">{children}</main>
      </div>
    </div>
  )
}
