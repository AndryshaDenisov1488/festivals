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
  LogOut
} from 'lucide-react'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'

type UserInfo = {
  user_id: number
  first_name?: string
  last_name?: string
  email?: string
  is_admin?: boolean
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

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      router.replace('/login')
      return
    }
    api<UserInfo>('/api/v1/users/me', { token })
      .then(setUser)
      .catch(() => {
        localStorage.removeItem('token')
        router.replace('/login')
      })
      .finally(() => setLoading(false))
  }, [router])

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

  return (
    <div className="flex min-h-screen">
      <aside className="flex w-56 flex-col border-r border-slate-200 bg-white">
        <div className="flex h-14 items-center border-b border-slate-200 px-4">
          <span className="font-semibold text-slate-800">Кабинет судьи</span>
        </div>
        <nav className="flex flex-1 flex-col space-y-1 p-2">
          {navItems.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className={cn(
                'flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition',
                pathname === href
                  ? 'bg-slate-100 font-medium text-slate-900'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          ))}
          {user?.is_admin && (
            <Link
              href="/dashboard/admin"
              className={cn(
                'flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition',
                pathname === '/dashboard/admin'
                  ? 'bg-slate-100 font-medium text-slate-900'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              )}
            >
              <Settings className="h-4 w-4" />
              Админ
            </Link>
          )}
          <div className="mt-auto border-t border-slate-200 pt-2">
            <button
              onClick={handleLogout}
              className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-600 transition hover:bg-slate-50 hover:text-slate-900"
            >
              <LogOut className="h-4 w-4" />
              Выйти
            </button>
          </div>
        </nav>
      </aside>
      <main className="flex-1 overflow-auto p-6">{children}</main>
    </div>
  )
}
