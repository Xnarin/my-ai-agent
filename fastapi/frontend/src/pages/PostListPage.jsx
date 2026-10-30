import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { Author, Feedback, formatDate } from '../components/Feedback'

const PAGE_SIZE = 10

export function PostListPage({ mine = false }) {
  const { token } = useAuth()
  const [params, setParams] = useSearchParams()
  const page = Math.max(1, Math.min(1000000, Number.parseInt(params.get('page'), 10) || 1))
  const search = params.get('search') || ''
  const order = params.get('order') === 'asc' ? 'asc' : 'desc'
  const [query, setQuery] = useState(search)
  const [data, setData] = useState({ items: [], total: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [revision, setRevision] = useState(0)
  const totalPages = Math.max(1, Math.ceil(data.total / PAGE_SIZE))

  useEffect(() => setQuery(search), [search, mine])
  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError('')
    api.posts({ search, order, offset: (page - 1) * PAGE_SIZE, limit: PAGE_SIZE }, mine ? token : null, controller.signal)
      .then((result) => {
        if (controller.signal.aborted) return
        const lastPage = Math.max(1, Math.ceil(result.total / PAGE_SIZE))
        if (page > lastPage) {
          setParams({ ...(search ? { search } : {}), order, page: String(lastPage) }, { replace: true })
        }
        setData(result)
      })
      .catch((reason) => { if (!controller.signal.aborted) setError(reason.message) })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [search, order, page, mine, token, revision, setParams])

  function updateParams(next) {
    setParams({ ...(search ? { search } : {}), order, page: '1', ...next })
  }

  return (
      <section aria-labelledby="board-title">
        <div className="section-heading"><h1 id="board-title">{mine ? '내 게시글' : '전체 게시글'} {!loading && !error && <span className="count">({data.total})</span>}</h1></div>
        <div className="board-toolbar">
          <form className="search-form" onSubmit={(event) => { event.preventDefault(); updateParams({ search: query.trim() }) }}>
            <label className="sr-only" htmlFor="search">게시글 제목 검색</label>
            <input id="search" type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="제목 검색" maxLength={200} />
            <button type="submit" className="button secondary">검색</button>
          </form>
          <label className="sort-control"><span className="sr-only">게시글 정렬</span><select value={order} onChange={(event) => updateParams({ order: event.target.value })}><option value="desc">최신순</option><option value="asc">오래된순</option></select></label>
        </div>
        {search && <div className="search-summary"><span>“{search}” 검색 결과</span><button className="text-button" onClick={() => updateParams({ search: '' })}>검색 초기화</button></div>}
        {loading ? <Feedback loading /> : error ? <Feedback error={error} retry={() => setRevision((value) => value + 1)} /> : data.items.length === 0 ?
          <Feedback title={search ? '검색 결과가 없습니다.' : '게시글이 없습니다.'} /> :
          <ul className="post-list">{data.items.map((post) => <li key={post.id}><Link to={`/posts/${post.id}`} className="post-row"><h2>{post.title}</h2><div className="post-meta"><Author user={post.user} />{formatDate(post.created_at) && <time dateTime={post.created_at}>{formatDate(post.created_at)}</time>}</div></Link></li>)}</ul>}
        {!loading && !error && data.total > 0 && <nav className="pagination" aria-label="게시글 페이지"><button className="button secondary" disabled={page <= 1} onClick={() => updateParams({ page: String(page - 1) })}>이전</button><span><strong>{page}</strong> / {totalPages}</span><button className="button secondary" disabled={page >= totalPages} onClick={() => updateParams({ page: String(page + 1) })}>다음</button></nav>}
      </section>
  )
}
