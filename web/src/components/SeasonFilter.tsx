'use client'

type SeasonOption = {
  key: string
  label: string
  is_current?: boolean
}

type SeasonFilterProps = {
  value: string
  onChange: (value: string) => void
  seasons: SeasonOption[]
  className?: string
}

export default function SeasonFilter({ value, onChange, seasons, className = '' }: SeasonFilterProps) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={`min-h-[44px] rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 ${className}`}
      aria-label="Сезон"
    >
      {seasons.map((season) => (
        <option key={season.key} value={season.key}>
          {season.label}
          {season.is_current ? ' (текущий)' : ''}
        </option>
      ))}
    </select>
  )
}
