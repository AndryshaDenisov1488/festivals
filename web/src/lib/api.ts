const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? ''

export async function api<T>(
  path: string,
  options?: RequestInit & { token?: string }
): Promise<T> {
  const { token, ...init } = options || {}
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(init.headers as Record<string, string>)
  }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${API_BASE}${path}`, { ...init, headers })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    const d = err.detail
    const msg = Array.isArray(d) && d.length > 0 ? d[0].msg : (typeof d === 'string' ? d : String(d ?? res.statusText))
    throw new Error(msg)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}
