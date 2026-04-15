'use client'

import { useEffect, useState } from 'react'
import { ChevronDown, ChevronUp, Users } from 'lucide-react'
import { api } from '@/lib/api'
import MonthFilter, { type MonthFilterValue } from '@/components/MonthFilter'

type Tournament = {
  tournament_id: number
  name: string
  date: string
  month: string
}

type ApprovedJudge = {
  user_id: number
  name: string
  function?: string | null
  category?: string | null
}

export default function FestmatesPage() {
  const [items, setItems] = useState<Tournament[]>([])
  const [loading, setLoading] = useState(true)
  const [monthFilter, setMonthFilter] = useState<MonthFilterValue>('future')
  const [search, setSearch] = useState('')
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [judgesByTournament, setJudgesByTournament] = useState<
    Record<number, ApprovedJudge[]>
  >({})
  const [loadingJudgesId, setLoadingJudgesId] = useState<number | null>(null)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) return
    const load = () => {
      const params = new URLSearchParams()
      params.set('my_approved_only', 'true')
      if (monthFilter === 'future') params.set('future_only', 'true')
      else if (monthFilter === 'all') params.set('future_only', 'false')
      else params.set('month', monthFilter)
      if (search.trim()) params.set('search', search.trim())
      setLoading(true)
      api<Tournament[]>(`/api/v1/tournaments?${params}`, { token })
        .then((tours) => {
          setItems(tours)
          setJudgesByTournament({})
          setExpandedId(null)
        })
        .catch(() => setItems([]))
        .finally(() => setLoading(false))
    }
    const id = search ? setTimeout(load, 200) : null
    if (!id) load()
    return () => {
      if (id) clearTimeout(id)
    }
  }, [monthFilter, search])

  const handleToggleJudges = async (tournamentId: number) => {
    if (expandedId === tournamentId) {
      setExpandedId(null)
      return
    }
    setExpandedId(tournamentId)
    if (judgesByTournament[tournamentId]) return
    const token = localStorage.getItem('token')
    if (!token) return
    setLoadingJudgesId(tournamentId)
    try {
      const list = await api<ApprovedJudge[]>(
        `/api/v1/tournaments/${tournamentId}/approved-judges`,
        { token }
      )
      setJudgesByTournament((prev) => ({ ...prev, [tournamentId]: list }))
    } catch {
      setJudgesByTournament((prev) => ({ ...prev, [tournamentId]: [] }))
    } finally {
      setLoadingJudgesId(null)
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
      </div>
    )
  }

  return (
    <div>
      <div className="mb-4 flex flex-col gap-4 md:mb-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-xl font-semibold text-slate-800 md:text-2xl">
              Кто ещё едет на фест
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              Турниры, на которые вы утверждены; список коллег по каждому фесту
            </p>
          </div>
          <MonthFilter value={monthFilter} onChange={setMonthFilter} />
        </div>
        <input
          type="search"
          placeholder="Поиск: название турнира или месяц..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Поиск турниров"
          className="min-h-[44px] max-w-md rounded-lg border border-slate-300 px-3 py-2.5 text-slate-800 placeholder:text-slate-400 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
        />
      </div>

      <div className="space-y-3">
        {items.map((t) => {
          const isOpen = expandedId === t.tournament_id
          const judges = judgesByTournament[t.tournament_id]
          const loadingRow = loadingJudgesId === t.tournament_id
          return (
            <div
              key={t.tournament_id}
              className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm"
            >
              <div className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0">
                  <p className="font-medium text-slate-800">{t.name}</p>
                  <p className="text-sm text-slate-500">
                    {t.date} · {t.month}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => handleToggleJudges(t.tournament_id)}
                  aria-expanded={isOpen}
                  className="inline-flex min-h-[44px] shrink-0 items-center justify-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm font-medium text-slate-800 transition hover:bg-slate-100"
                >
                  <Users className="h-4 w-4" aria-hidden />
                  {isOpen ? 'Скрыть список' : 'Утверждённые судьи'}
                  {isOpen ? (
                    <ChevronUp className="h-4 w-4" aria-hidden />
                  ) : (
                    <ChevronDown className="h-4 w-4" aria-hidden />
                  )}
                </button>
              </div>
              {isOpen && (
                <div className="border-t border-slate-100 bg-slate-50/80 px-4 py-3">
                  {loadingRow && (
                    <p className="text-sm text-slate-500">Загрузка...</p>
                  )}
                  {!loadingRow && judges && judges.length === 0 && (
                    <p className="text-sm text-slate-600">
                      На этот турнир пока нет утверждённых судей.
                    </p>
                  )}
                  {!loadingRow && judges && judges.length > 0 && (
                    <ul className="space-y-2" role="list">
                      {judges.map((j) => (
                        <li
                          key={j.user_id}
                          className="text-sm text-slate-800"
                        >
                          <span className="font-medium">{j.name}</span>
                          {j.function ? (
                            <span className="text-slate-600">
                              {' '}
                              — {j.function}
                            </span>
                          ) : null}
                          {j.category ? (
                            <span className="text-slate-500">
                              {' '}
                              ({j.category})
                            </span>
                          ) : null}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </div>
          )
        })}
        {items.length === 0 && (
          <p className="py-8 text-center text-slate-500">
            Нет турниров, на которые вы утверждены — здесь видны только такие фесты.
          </p>
        )}
      </div>
    </div>
  )
}
