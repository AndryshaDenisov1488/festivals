'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Trophy } from 'lucide-react'

export default function HomePage() {
  const router = useRouter()
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
    if (token) {
      router.replace('/dashboard')
    } else {
      setChecking(false)
    }
  }, [router])

  if (checking) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-br from-slate-50 via-white to-slate-100">
      <header className="border-b border-slate-200/60 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-4 sm:px-6">
          <div className="flex items-center gap-2">
            <div className="rounded-lg bg-slate-800 p-2">
              <Trophy className="h-6 w-6 text-white" />
            </div>
            <span className="text-xl font-bold tracking-tight text-slate-800">Кабинет судьи</span>
          </div>
          <Link
            href="/login"
            className="rounded-lg bg-slate-800 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-700"
          >
            Войти
          </Link>
        </div>
      </header>

      <main className="flex flex-1 flex-col items-center justify-center px-4 py-16 sm:py-24">
        <div className="mx-auto max-w-2xl text-center">
          <h1 className="mb-4 text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
            Платформа для судей
          </h1>
          <p className="mb-10 text-lg text-slate-600 sm:text-xl">
            Управляйте заявками на турниры, судите фестивали, радуйтесь жизни.
          </p>
          <Link
            href="/login"
            className="inline-flex items-center gap-2 rounded-xl bg-slate-800 px-8 py-4 text-lg font-semibold text-white shadow-lg transition hover:bg-slate-700 hover:shadow-xl"
          >
            Войти в кабинет
          </Link>
        </div>
      </main>

      <footer className="border-t border-slate-200/60 py-6">
        <p className="text-center text-sm text-slate-500">
          Веб-портал судей · Фестивальчики для судей
        </p>
      </footer>
    </div>
  )
}
