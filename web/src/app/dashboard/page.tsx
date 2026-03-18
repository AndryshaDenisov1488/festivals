'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Trophy, ClipboardList, Wallet } from 'lucide-react'
import { api } from '@/lib/api'

type Summary = {
  registrations_count?: number
  earnings_total?: number
  tournaments_count?: number
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<Summary | null>(null)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) return
    Promise.all([
      api<unknown[]>('/api/v1/registrations/my', { token }).catch(() => []),
      api<{ total_amount?: number }>('/api/v1/earnings/my/summary', { token }).catch(() => ({})),
      api<unknown[]>('/api/v1/tournaments', { token }).catch(() => [])
    ]).then(([regs, earn, tours]) => {
      const earnData = earn as { total_amount?: number } | undefined
      setSummary({
        registrations_count: Array.isArray(regs) ? regs.length : 0,
        earnings_total: earnData?.total_amount ?? 0,
        tournaments_count: Array.isArray(tours) ? tours.length : 0
      })
    })
  }, [])

  const cards = [
    { href: '/dashboard/tournaments', label: 'Турниры', icon: Trophy, value: summary?.tournaments_count ?? '—' },
    { href: '/dashboard/registrations', label: 'Мои заявки', icon: ClipboardList, value: summary?.registrations_count ?? '—' },
    { href: '/dashboard/earnings', label: 'Выплаты', icon: Wallet, value: summary?.earnings_total != null ? `${summary.earnings_total} ₽` : '—' }
  ]

  return (
    <div>
      <h1 className="mb-4 text-xl font-semibold text-slate-800 md:mb-6 md:text-2xl">Обзор</h1>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {cards.map(({ href, label, icon: Icon, value }) => (
          <Link
            key={href}
            href={href}
            className="flex min-h-[88px] items-center gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition hover:border-slate-300 hover:shadow active:bg-slate-50"
          >
            <div className="rounded-lg bg-slate-100 p-3">
              <Icon className="h-6 w-6 text-slate-600" />
            </div>
            <div>
              <p className="text-sm text-slate-500">{label}</p>
              <p className="text-xl font-semibold text-slate-800">{value}</p>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
