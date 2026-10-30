export function Feedback({ loading, error, retry, title, children }) {
  if (loading) return <div className="feedback" role="status">불러오는 중…</div>
  if (error) return (
    <div className="feedback error-box" role="alert">
      <p>{error}</p>
      {retry && <button className="button secondary" onClick={retry}>다시 시도</button>}
    </div>
  )
  return <div className="feedback"><strong>{title}</strong>{children && <p>{children}</p>}</div>
}

export function Author({ user }) {
  const name = user?.email || '알 수 없는 사용자'
  return <span className="author">{name}</span>
}

export function formatDate(value) {
  if (!value || Number.isNaN(new Date(value).getTime())) return null
  return new Intl.DateTimeFormat('ko-KR', { dateStyle: 'medium' }).format(new Date(value))
}
