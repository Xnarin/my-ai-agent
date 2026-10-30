import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'

export function NewPostPage() {
  const { token } = useAuth()
  const navigate = useNavigate()
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [error, setError] = useState('')
  const [pending, setPending] = useState(false)

  async function submit(event) {
    event.preventDefault()
    if (pending) return
    if (!title.trim() || !content.trim()) { setError('제목과 내용을 입력해 주세요.'); return }
    setPending(true)
    setError('')
    try {
      const post = await api.createPost({ title: title.trim(), content: content.trim() }, token)
      navigate(`/posts/${post.id}`, { replace: true })
    } catch (reason) {
      setError(reason.message)
    } finally {
      setPending(false)
    }
  }

  return (
    <div className="reading-width">
      <Link className="back-link" to="/">목록</Link>
      <h1 className="section-heading">글쓰기</h1>
      <form className="stack-form" onSubmit={submit}>
        {error && <p className="form-error" role="alert">{error}</p>}
        <label htmlFor="post-title">제목<input id="post-title" value={title} onChange={(event) => setTitle(event.target.value)} maxLength={50} required disabled={pending} aria-describedby="title-count" /></label><span id="title-count" className="character-count">{title.length} / 50</span>
        <label htmlFor="post-content">내용<textarea id="post-content" value={content} onChange={(event) => setContent(event.target.value)} rows={12} required disabled={pending} /></label>
        <div className="form-actions"><Link className="button secondary" to="/">취소</Link><button type="submit" className="button" disabled={pending || !title.trim() || !content.trim()}>{pending ? '등록 중…' : '등록'}</button></div>
      </form>
    </div>
  )
}
