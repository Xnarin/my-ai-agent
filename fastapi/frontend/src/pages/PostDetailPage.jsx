import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { Author, Feedback, formatDate } from '../components/Feedback'

function Comments({ postId }) {
  const { user, token } = useAuth()
  const [comments, setComments] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [submitError, setSubmitError] = useState('')
  const [content, setContent] = useState('')
  const [pending, setPending] = useState(false)
  const [revision, setRevision] = useState(0)
  const [notice, setNotice] = useState('')

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setLoadError('')
    api.comments(postId, controller.signal)
      .then((data) => { if (!controller.signal.aborted) setComments(data) })
      .catch((reason) => { if (!controller.signal.aborted) setLoadError(reason.status === 404 ? '댓글을 불러올 수 없습니다. 잠시 후 다시 시도해 주세요.' : reason.message) })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [postId, revision])

  async function submit(event) {
    event.preventDefault()
    if (pending || !content.trim()) return
    setPending(true)
    setSubmitError('')
    setNotice('')
    try {
      await api.createComment(postId, { content: content.trim() }, token)
      setContent('')
      setNotice('댓글이 등록되었습니다.')
      setRevision((value) => value + 1)
    } catch (reason) {
      setSubmitError(reason.message)
    } finally {
      setPending(false)
    }
  }

  return (
    <section className="comments-section" aria-labelledby="comments-title">
      <h2 id="comments-title">댓글 {!loading && !loadError && <span className="count">({comments.length})</span>}</h2>
      {user ? <form className="comment-form" onSubmit={submit}><label className="sr-only" htmlFor="comment">댓글 내용</label><textarea id="comment" value={content} onChange={(event) => setContent(event.target.value)} placeholder="댓글 입력" rows={3} required disabled={pending} /><div className="form-actions"><button className="button" type="submit" disabled={pending || !content.trim()}>{pending ? '등록 중…' : '댓글 등록'}</button></div>{submitError && <p className="form-error" role="alert">{submitError}</p>}{notice && <p className="success-message" role="status">{notice}</p>}</form> : <div className="login-prompt"><span>댓글 작성은 로그인이 필요합니다.</span><Link to="/login" state={{ from: `/posts/${postId}` }}>로그인</Link></div>}
      {loading ? <Feedback loading /> : loadError ? <Feedback error={loadError} retry={() => setRevision((value) => value + 1)} /> : comments.length === 0 ? <Feedback title="댓글이 없습니다." /> : <ul className="comment-list">{comments.map((comment) => <li key={comment.id}><div className="post-meta"><Author user={comment.user} />{formatDate(comment.created_at) && <time dateTime={comment.created_at}>{formatDate(comment.created_at)}</time>}</div><p>{comment.content}</p></li>)}</ul>}
    </section>
  )
}

export function PostDetailPage() {
  const { postId } = useParams()
  const [post, setPost] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [revision, setRevision] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError('')
    api.post(postId, controller.signal)
      .then((data) => { if (!controller.signal.aborted) setPost(data) })
      .catch((reason) => { if (!controller.signal.aborted) setError(reason.message) })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [postId, revision])

  return <div className="reading-width"><Link className="back-link" to="/">목록</Link>{loading ? <Feedback loading /> : error ? <Feedback error={error} retry={() => setRevision((value) => value + 1)} /> : post && <><article className="post-detail"><h1>{post.title}</h1><div className="post-meta"><Author user={post.user} />{formatDate(post.created_at) && <time dateTime={post.created_at}>{formatDate(post.created_at)}</time>}</div><div className="post-content">{post.content}</div></article><Comments key={postId} postId={postId} /></>}</div>
}
