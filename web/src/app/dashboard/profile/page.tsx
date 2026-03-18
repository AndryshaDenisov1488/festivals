'use client'

import { useEffect, useState } from 'react'
import { api } from '@/lib/api'

type User = {
  user_id: number
  first_name?: string
  last_name?: string
  function?: string
  category?: string
  email?: string
  is_admin?: boolean
  has_password?: boolean
}

export default function ProfilePage() {
  const [user, setUser] = useState<User | null>(null)
  const [editMode, setEditMode] = useState(false)
  const [form, setForm] = useState({ first_name: '', last_name: '', function: '', category: '' })
  const [profileError, setProfileError] = useState('')
  const [profileSaving, setProfileSaving] = useState(false)

  const [showPasswordModal, setShowPasswordModal] = useState(false)
  const [showSetPasswordModal, setShowSetPasswordModal] = useState(false)
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordError, setPasswordError] = useState('')
  const [passwordSaving, setPasswordSaving] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) return
    api<User>('/api/v1/users/me', { token })
      .then((u) => {
        setUser(u)
        setForm({
          first_name: u.first_name ?? '',
          last_name: u.last_name ?? '',
          function: u.function ?? '',
          category: u.category ?? ''
        })
      })
      .catch(() => setUser(null))
  }, [])

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setProfileError('')
    const token = localStorage.getItem('token')
    if (!token) return
    setProfileSaving(true)
    try {
      await api('/api/v1/users/me', {
        method: 'PATCH',
        body: JSON.stringify(form),
        token
      })
      setUser((prev) => (prev ? { ...prev, ...form } : prev))
      setEditMode(false)
    } catch (err) {
      setProfileError(err instanceof Error ? err.message : 'Ошибка сохранения')
    } finally {
      setProfileSaving(false)
    }
  }

  const handleSetPasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setPasswordError('')
    if (newPassword.length < 8) {
      setPasswordError('Пароль должен быть не менее 8 символов')
      return
    }
    if (newPassword !== confirmPassword) {
      setPasswordError('Пароли не совпадают')
      return
    }
    const token = localStorage.getItem('token')
    if (!token) return
    setPasswordSaving(true)
    try {
      await api('/api/v1/auth/set-password', {
        method: 'POST',
        body: JSON.stringify({ password: newPassword }),
        token
      })
      setShowSetPasswordModal(false)
      setNewPassword('')
      setConfirmPassword('')
      setUser((prev) => (prev ? { ...prev, has_password: true } : prev))
    } catch (err) {
      setPasswordError(err instanceof Error ? err.message : 'Ошибка сохранения')
    } finally {
      setPasswordSaving(false)
    }
  }

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setPasswordError('')
    if (newPassword.length < 8) {
      setPasswordError('Пароль должен быть не менее 8 символов')
      return
    }
    if (newPassword !== confirmPassword) {
      setPasswordError('Пароли не совпадают')
      return
    }
    const token = localStorage.getItem('token')
    if (!token) return
    setPasswordSaving(true)
    try {
      await api('/api/v1/auth/change-password', {
        method: 'POST',
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
        token
      })
      setShowPasswordModal(false)
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (err) {
      setPasswordError(err instanceof Error ? err.message : 'Ошибка смены пароля')
    } finally {
      setPasswordSaving(false)
    }
  }

  if (!user) {
    return (
      <div className="flex justify-center py-12">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
      </div>
    )
  }

  const inputClass = "min-h-[44px] w-full rounded-lg border border-slate-300 px-3 py-2.5 text-slate-800 placeholder:text-slate-400 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500 disabled:opacity-50"

  return (
    <div>
      <h1 className="mb-4 text-xl font-semibold text-slate-800 md:mb-6 md:text-2xl">Профиль</h1>

      <div className="max-w-md space-y-6">
        {/* Редактирование данных */}
        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-medium text-slate-800">Данные профиля</h2>
            {!editMode ? (
              <button
                onClick={() => setEditMode(true)}
                className="min-h-[44px] rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                Изменить
              </button>
            ) : (
              <button
                onClick={() => {
                  setEditMode(false)
                  setForm({
                    first_name: user.first_name ?? '',
                    last_name: user.last_name ?? '',
                    function: user.function ?? '',
                    category: user.category ?? ''
                  })
                }}
                className="min-h-[44px] rounded-lg border border-slate-300 px-4 py-2.5 text-sm text-slate-600 hover:bg-slate-50"
              >
                Отмена
              </button>
            )}
          </div>

          {editMode ? (
            <form onSubmit={handleProfileSubmit} className="space-y-4">
              <div>
                <label htmlFor="first_name" className="mb-1 block text-sm font-medium text-slate-600">
                  Имя
                </label>
                <input
                  id="first_name"
                  type="text"
                  value={form.first_name}
                  onChange={(e) => setForm((f) => ({ ...f, first_name: e.target.value }))}
                  placeholder="Андрей"
                  required
                  minLength={2}
                  maxLength={30}
                  className={inputClass}
                  disabled={profileSaving}
                  autoComplete="given-name"
                />
                <p className="mt-1 text-xs text-slate-500">Буквы и дефис, 2–30 символов</p>
              </div>
              <div>
                <label htmlFor="last_name" className="mb-1 block text-sm font-medium text-slate-600">
                  Фамилия
                </label>
                <input
                  id="last_name"
                  type="text"
                  value={form.last_name}
                  onChange={(e) => setForm((f) => ({ ...f, last_name: e.target.value }))}
                  placeholder="Иванов"
                  required
                  minLength={2}
                  maxLength={30}
                  className={inputClass}
                  disabled={profileSaving}
                  autoComplete="family-name"
                />
              </div>
              <div>
                <label htmlFor="function" className="mb-1 block text-sm font-medium text-slate-600">
                  Судейская функция
                </label>
                <input
                  id="function"
                  type="text"
                  value={form.function}
                  onChange={(e) => setForm((f) => ({ ...f, function: e.target.value }))}
                  placeholder="Главный судья"
                  required
                  minLength={2}
                  className={inputClass}
                  disabled={profileSaving}
                />
              </div>
              <div>
                <label htmlFor="category" className="mb-1 block text-sm font-medium text-slate-600">
                  Категория
                </label>
                <input
                  id="category"
                  type="text"
                  value={form.category}
                  onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
                  placeholder="1 категория"
                  required
                  className={inputClass}
                  disabled={profileSaving}
                />
              </div>
              {profileError && <p className="text-sm text-red-600">{profileError}</p>}
              <button
                type="submit"
                disabled={profileSaving}
                className="min-h-[44px] w-full rounded-lg bg-slate-800 py-2.5 font-medium text-white hover:bg-slate-700 disabled:opacity-50"
              >
                {profileSaving ? 'Сохранение...' : 'Сохранить'}
              </button>
            </form>
          ) : (
            <div className="space-y-4">
              <div>
                <p className="text-sm text-slate-500">Имя</p>
                <p className="font-medium text-slate-800">
                  {[user.first_name, user.last_name].filter(Boolean).join(' ') || '—'}
                </p>
              </div>
              {(user.function || user.category) && (
                <div>
                  <p className="text-sm text-slate-500">Функция / Категория</p>
                  <p className="font-medium text-slate-800">
                    {[user.function, user.category].filter(Boolean).join(' · ') || '—'}
                  </p>
                </div>
              )}
              <div>
                <p className="text-sm text-slate-500">Email</p>
                <p className="font-medium text-slate-800">{user.email || '—'}</p>
                <p className="mt-1 text-xs text-slate-500">Привязать email можно в Telegram-боте</p>
              </div>
              {user.is_admin && (
                <p className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">Администратор</p>
              )}
            </div>
          )}
        </section>

        {/* Пароль */}
        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-2 font-medium text-slate-800">Пароль</h2>
          <p className="mb-4 text-sm text-slate-500">
            {user.has_password
              ? 'Пароль задан. Вы можете войти по email и паролю.'
              : 'Пароль не задан. Задайте пароль для входа по email.'}
          </p>
          {user.has_password ? (
            <button
              onClick={() => setShowPasswordModal(true)}
              className="min-h-[44px] rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Сменить пароль
            </button>
          ) : (
            <button
              onClick={() => setShowSetPasswordModal(true)}
              className="min-h-[44px] rounded-lg bg-slate-800 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-700"
            >
              Задать пароль
            </button>
          )}
        </section>
      </div>

      {showSetPasswordModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
          onClick={() => !passwordSaving && setShowSetPasswordModal(false)}
        >
          <div
            className="w-full max-w-sm rounded-xl bg-white p-6 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="mb-2 text-lg font-semibold text-slate-800">Задать пароль</h3>
            <p className="mb-4 text-sm text-slate-500">
              Пароль нужен для входа по email и паролю. Минимум 8 символов.
            </p>
            <form onSubmit={handleSetPasswordSubmit} className="space-y-4">
              <div>
                <label htmlFor="set-new-password" className="mb-1 block text-sm font-medium text-slate-600">
                  Пароль
                </label>
                <input
                  id="set-new-password"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  minLength={8}
                  placeholder="Минимум 8 символов"
                  className={inputClass}
                  disabled={passwordSaving}
                  autoComplete="new-password"
                />
              </div>
              <div>
                <label htmlFor="set-confirm-password" className="mb-1 block text-sm font-medium text-slate-600">
                  Повторите пароль
                </label>
                <input
                  id="set-confirm-password"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  minLength={8}
                  className={inputClass}
                  disabled={passwordSaving}
                  autoComplete="new-password"
                />
              </div>
              {passwordError && <p className="text-sm text-red-600">{passwordError}</p>}
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={passwordSaving}
                  className="min-h-[44px] flex-1 rounded-lg bg-slate-800 py-2.5 font-medium text-white hover:bg-slate-700 disabled:opacity-50"
                >
                  {passwordSaving ? 'Сохранение...' : 'Сохранить'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowSetPasswordModal(false)}
                  disabled={passwordSaving}
                  className="min-h-[44px] rounded-lg border border-slate-300 px-4 py-2.5 hover:bg-slate-50 disabled:opacity-50"
                >
                  Отмена
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showPasswordModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
          onClick={() => !passwordSaving && setShowPasswordModal(false)}
        >
          <div
            className="w-full max-w-sm rounded-xl bg-white p-6 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="mb-2 text-lg font-semibold text-slate-800">Сменить пароль</h3>
            <form onSubmit={handlePasswordSubmit} className="space-y-4">
              <div>
                <label htmlFor="current-password" className="mb-1 block text-sm font-medium text-slate-600">
                  Текущий пароль
                </label>
                <input
                  id="current-password"
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  required
                  className={inputClass}
                  disabled={passwordSaving}
                  autoComplete="current-password"
                />
              </div>
              <div>
                <label htmlFor="new-password" className="mb-1 block text-sm font-medium text-slate-600">
                  Новый пароль
                </label>
                <input
                  id="new-password"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  minLength={8}
                  placeholder="Минимум 8 символов"
                  className={inputClass}
                  disabled={passwordSaving}
                  autoComplete="new-password"
                />
              </div>
              <div>
                <label htmlFor="confirm-password" className="mb-1 block text-sm font-medium text-slate-600">
                  Повторите новый пароль
                </label>
                <input
                  id="confirm-password"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  minLength={8}
                  className={inputClass}
                  disabled={passwordSaving}
                  autoComplete="new-password"
                />
              </div>
              {passwordError && <p className="text-sm text-red-600">{passwordError}</p>}
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={passwordSaving}
                  className="min-h-[44px] flex-1 rounded-lg bg-slate-800 py-2.5 font-medium text-white hover:bg-slate-700 disabled:opacity-50"
                >
                  {passwordSaving ? 'Сохранение...' : 'Сохранить'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowPasswordModal(false)}
                  disabled={passwordSaving}
                  className="min-h-[44px] rounded-lg border border-slate-300 px-4 py-2.5 hover:bg-slate-50 disabled:opacity-50"
                >
                  Отмена
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
