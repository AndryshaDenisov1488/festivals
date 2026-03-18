'use client'

import { useEffect, useState } from 'react'
import { notFound } from 'next/navigation'
import { api } from '@/lib/api'

type UserInfo = {
  is_admin?: boolean
}

export default function AdminGuard({ children }: { children: React.ReactNode }) {
  const [checked, setChecked] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      notFound()
      return
    }
    api<UserInfo>('/api/v1/users/me', { token })
      .then((user) => {
        if (!user?.is_admin) {
          notFound()
        } else {
          setChecked(true)
        }
      })
      .catch(() => {
        notFound()
      })
  }, [])

  if (!checked) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
      </div>
    )
  }

  return <>{children}</>
}
