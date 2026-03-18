import Link from 'next/link'
import { Home, ArrowLeft, SearchX } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 px-4">
      <div className="relative">
        <span className="absolute -inset-4 animate-pulse rounded-full bg-amber-500/10 blur-2xl" aria-hidden />
        <div className="relative flex flex-col items-center text-center">
          <div className="mb-6 flex h-24 w-24 items-center justify-center rounded-2xl border-2 border-amber-500/30 bg-amber-500/5">
            <SearchX className="h-12 w-12 text-amber-400" strokeWidth={1.5} />
          </div>
          <p className="mb-2 font-mono text-6xl font-bold tabular-nums text-amber-400/90 md:text-7xl">
            404
          </p>
          <h1 className="mb-3 text-xl font-semibold text-slate-200 md:text-2xl">
            Страница не найдена
          </h1>
          <p className="mb-10 max-w-sm text-slate-400">
            Такой страницы не существует. Возможно, вы перешли по устаревшей ссылке или ошиблись адресом.
          </p>
          <div className="flex flex-col gap-3 sm:flex-row">
            <Link
              href="/dashboard"
              className="inline-flex min-h-[48px] items-center justify-center gap-2 rounded-xl border border-amber-500/40 bg-amber-500/10 px-6 font-medium text-amber-300 transition hover:bg-amber-500/20 hover:border-amber-500/60"
            >
              <ArrowLeft className="h-5 w-5" />
              Назад в кабинет
            </Link>
            <Link
              href="/"
              className="inline-flex min-h-[48px] items-center justify-center gap-2 rounded-xl border border-slate-600 bg-slate-800/50 px-6 font-medium text-slate-200 transition hover:bg-slate-700/50"
            >
              <Home className="h-5 w-5" />
              На главную
            </Link>
          </div>
        </div>
      </div>
      <p className="mt-16 text-center font-mono text-xs text-slate-500">
        ERROR 404 · PAGE NOT FOUND
      </p>
    </div>
  )
}
