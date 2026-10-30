import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ai, featureError, mergeMessages } from '../api/ai'
import { Feedback, formatDate } from './Feedback'

export function RoomSidebar({ token, roomId, revision, onCreate, creating, onSelect, open }) {
  const [query, setQuery] = useState('')
  const [search, setSearch] = useState('')
  const [order, setOrder] = useState('desc')
  const [offset, setOffset] = useState(0)
  const [retry, setRetry] = useState(0)
  const [data, setData] = useState({ items: [], total: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => { setOffset(0) }, [revision])
  useEffect(() => {
    const controller = new AbortController()
    setLoading(true); setError('')
    if (offset === 0) setData({ items: [], total: 0 })
    ai.rooms({ search, order, offset, limit: 20 }, token, controller.signal)
      .then((result) => { if (!controller.signal.aborted) setData((current) => ({ ...result, items: offset === 0 ? result.items : mergeMessages(current.items, result.items) })) })
      .catch((reason) => { if (!controller.signal.aborted) setError(featureError(reason, '채팅방 기능')) })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [search, order, offset, token, revision, retry])

  return <aside id="room-sidebar" className={`room-sidebar ${open ? 'is-open' : ''}`} aria-label="채팅방 관리">
    <div className="sidebar-heading"><h2>내 채팅방</h2><span>{data.total}</span><button className="text-button sidebar-close" onClick={onSelect}>닫기</button></div>
    <button className="button new-chat" disabled={creating} onClick={onCreate}>{creating ? '만드는 중…' : '새 채팅'}</button>
    <form className="room-search" onSubmit={(event) => { event.preventDefault(); setSearch(query.trim()); setOffset(0); setRetry((value) => value + 1) }}>
      <label className="sr-only" htmlFor="room-search">채팅방 검색</label><input id="room-search" type="search" placeholder="채팅방 검색" value={query} maxLength={100} onChange={(event) => setQuery(event.target.value)} /><button className="text-button" type="submit">검색</button>
    </form>
    <label className="room-sort"><span>목록 정렬</span><select value={order} onChange={(event) => { setOrder(event.target.value); setOffset(0) }}><option value="desc">최근 대화순</option><option value="asc">오래된 대화순</option></select></label>
    <div className="room-list-area">
      <ul className="room-list">{data.items.map((room) => <li key={room.id}><Link to={`/chat/${encodeURIComponent(room.id)}`} onClick={onSelect} aria-current={String(room.id) === roomId ? 'page' : undefined} className={String(room.id) === roomId ? 'selected' : ''}><span className="room-label"><strong>{room.title}</strong><span>{formatDate(room.updated_at || room.created_at)}</span></span></Link></li>)}</ul>
      {loading && <Feedback loading />}
      {error && <Feedback error={error} retry={() => setRetry((value) => value + 1)} />}
      {!loading && !error && !data.items.length && <Feedback title={search ? '검색 결과가 없습니다.' : '아직 채팅방이 없어요.'}>{search ? '다른 제목으로 검색해 보세요.' : '새 채팅으로 대화를 시작하세요.'}</Feedback>}
      {!error && data.items.length < data.total && <button className="text-button load-rooms" disabled={loading} onClick={() => setOffset((value) => value + 20)}>채팅방 더 불러오기</button>}
    </div>
  </aside>
}
