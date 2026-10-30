import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'

export function AuthPage({ signup = false }) {
  const auth = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [error, setError] = useState('')
  const [pending, setPending] = useState(false)
  const requestedPath = location.state?.from
  const from = typeof requestedPath === 'string' && requestedPath.startsWith('/') && !requestedPath.startsWith('//') && !['/login', '/signup'].includes(requestedPath) ? requestedPath : '/'

  if (auth.user) return <Navigate to={from} replace />

  async function submit(event) {
    event.preventDefault()
    if (pending) return
    const form = new FormData(event.currentTarget)
    const credentials = { email: form.get('email').trim(), password: form.get('password') }
    setPending(true)
    setError('')
    try {
      if (signup) {
        await api.signup(credentials)
        navigate('/login', { replace: true, state: { from, message: '회원가입이 완료되었습니다. 로그인해 주세요.' } })
      } else {
        await auth.login(credentials)
        navigate(from, { replace: true })
      }
    } catch (reason) {
      setError(reason.message)
    } finally {
      setPending(false)
    }
  }

  return (
      <section className="auth-form" key={signup ? 'signup' : 'login'} aria-labelledby="auth-title">
        <h1 id="auth-title">{signup ? '회원가입' : '로그인'}</h1>
        {location.state?.message && <p className="success-message" role="status">{location.state.message}</p>}
        {error && <p className="form-error" role="alert">{error}</p>}
        <form className="stack-form" onSubmit={submit}>
          <label htmlFor="email">이메일<input id="email" name="email" type="email" autoComplete="username" placeholder="you@example.com" maxLength={254} required disabled={pending} /></label>
          <label htmlFor="password">비밀번호<input id="password" name="password" type="password" autoComplete={signup ? 'new-password' : 'current-password'} minLength={signup ? 8 : 1} maxLength={128} required disabled={pending} aria-describedby={signup ? 'password-hint' : undefined} /></label>
          {signup && <p id="password-hint" className="field-hint">비밀번호 8~128자</p>}
          <button className="button full-width" type="submit" disabled={pending || auth.loading}>{pending ? '처리 중…' : signup ? '가입하기' : '로그인'}</button>
        </form>
        <p className="auth-switch"><Link to={signup ? '/login' : '/signup'} state={{ from }} onClick={() => setError('')}>{signup ? '로그인' : '회원가입'}</Link></p>
      </section>
  )
}
