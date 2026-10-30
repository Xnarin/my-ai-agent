import { createContext, useContext, useEffect, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { api, SESSION_EXPIRED_EVENT, TOKEN_KEY } from '../api/client'
import { Feedback } from '../components/Feedback'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => sessionStorage.getItem(TOKEN_KEY))
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(Boolean(token))
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [revision, setRevision] = useState(0)

  function logout() {
    sessionStorage.removeItem(TOKEN_KEY)
    setToken(null)
    setUser(null)
    setError('')
    setLoading(false)
  }

  useEffect(() => {
    function expire() {
      logout()
      setNotice('로그인 시간이 만료되었습니다. 다시 로그인해 주세요.')
    }
    window.addEventListener(SESSION_EXPIRED_EVENT, expire)
    return () => window.removeEventListener(SESSION_EXPIRED_EVENT, expire)
  }, [])

  useEffect(() => {
    if (!token) return
    const controller = new AbortController()
    setLoading(true)
    setError('')
    api.me(token, controller.signal)
      .then((data) => { if (!controller.signal.aborted) setUser(data) })
      .catch((reason) => {
        if (!controller.signal.aborted && reason.status !== 401) setError(reason.message)
      })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [token, revision])

  async function login(credentials) {
    const result = await api.login(credentials)
    if (!result?.access_token) throw new Error('로그인 응답에 인증 정보가 없습니다.')
    const currentUser = await api.me(result.access_token)
    sessionStorage.setItem(TOKEN_KEY, result.access_token)
    setUser(currentUser)
    setToken(result.access_token)
    setError('')
    setNotice('')
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, error, notice, login, logout,
      clearNotice: () => setNotice(''), retry: () => setRevision((value) => value + 1) }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}

export function RequireAuth({ children }) {
  const auth = useAuth()
  const location = useLocation()
  if (auth.loading) return <Feedback loading />
  if (auth.error) return <Feedback error={auth.error} retry={auth.retry} />
  if (!auth.user) return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />
  return children
}
