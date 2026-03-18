'use client'

const MONTHS = [
  'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
]

export type MonthFilterValue = 'future' | 'all' | string

type MonthFilterProps = {
  value: MonthFilterValue
  onChange: (value: MonthFilterValue) => void
  showFutureOption?: boolean
  showAllOption?: boolean
  label?: string
}

export default function MonthFilter({
  value,
  onChange,
  showFutureOption = true,
  showAllOption = true,
  label = 'Период'
}: MonthFilterProps) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      {label && (
        <span className="text-sm font-medium text-slate-600">{label}:</span>
      )}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as MonthFilterValue)}
        className="min-h-[44px] rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-400/30"
        aria-label={label}
      >
        {showFutureOption && (
          <option value="future">Будущие</option>
        )}
        {showAllOption && (
          <option value="all">Все</option>
        )}
        {MONTHS.map((m) => (
          <option key={m} value={m}>{m}</option>
        ))}
      </select>
    </div>
  )
}
