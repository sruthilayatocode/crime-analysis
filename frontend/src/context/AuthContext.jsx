import { createContext, useCallback, useEffect, useMemo, useState } from 'react'
import { fetchCurrentUser, loginUser, logoutUser, registerUser } from '../services/api'
import { normalizeRole } from '../utils/roles'

const STORAGE_KEY = 'crimesense.session'

export const AuthContext = createContext(null)

function readStoredSession() {
  if (typeof window === 'undefined') return { user: null, token: null }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)

    if (!raw) return { user: null, token: null }

    const stored = JSON.parse(raw)

    if (!stored?.token || !stored?.user) return { user: null, token: null }

    return {
      user: { ...stored.user, role: normalizeRole(stored.user.role) },
      token: stored.token,
    }
  } catch {
    return { user: null, token: null }
  }
}

function withNormalizedRole(user) {
  return { ...user, role: normalizeRole(user?.role) }
}

export function AuthProvider({ children }) {
  // Read synchronously so the very first render already knows
  // who is signed in - this avoids a redirect flash on reload.
  const [session, setSession] = useState(readStoredSession)
  const [submitting, setSubmitting] = useState(false)

  const persist = useCallback((next) => {
    setSession(next)

    try {
      if (next.token && next.user) {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
      } else {
        window.localStorage.removeItem(STORAGE_KEY)
      }
    } catch {
      // Storage can be unavailable (private mode); keep the
      // session in memory only.
    }
  }, [])

  const login = useCallback(
    async (email, password) => {
      setSubmitting(true)

      try {
        const result = await loginUser(email, password)
        const user = withNormalizedRole(result.user)

        persist({ user, token: result.token })

        return user
      } finally {
        setSubmitting(false)
      }
    },
    [persist]
  )

  const register = useCallback(
    async (payload) => {
      setSubmitting(true)

      try {
        const result = await registerUser(payload)
        const user = withNormalizedRole(result.user)

        persist({ user, token: result.token })

        return user
      } finally {
        setSubmitting(false)
      }
    },
    [persist]
  )

  const logout = useCallback(() => {
    const activeToken = session.token

    persist({ user: null, token: null })

    if (activeToken) {
      // Best effort: tokens are stateless, so a failure here does
      // not keep the client signed in.
      logoutUser(activeToken).catch(() => {})
    }
  }, [persist, session.token])

  // Validate the stored token once and refresh the account data.
  useEffect(() => {
    if (!session.token) return undefined

    let cancelled = false

    fetchCurrentUser(session.token)
      .then((result) => {
        if (cancelled) return

        persist({
          user: withNormalizedRole(result.user),
          token: session.token,
        })
      })
      .catch((error) => {
        if (cancelled) return

        // 401 means the token expired or was revoked.
        if (error.status === 401) persist({ user: null, token: null })
        // Any other failure (backend offline) keeps the optimistic
        // session so the UI still works.
      })

    return () => {
      cancelled = true
    }
  }, [session.token, persist])

  const value = useMemo(
    () => ({
      user: session.user,
      token: session.token,
      role: session.user?.role ?? null,
      isAuthenticated: Boolean(session.token && session.user),
      submitting,
      login,
      register,
      logout,
    }),
    [session, submitting, login, register, logout]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
