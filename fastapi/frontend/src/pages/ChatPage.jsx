import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { ai, featureError } from '../api/ai'
import { Conversation } from '../components/Conversation'
import { RoomSidebar } from '../components/RoomSidebar'

export function ChatPage() {
  const { token } = useAuth()
  const { roomId } = useParams()
  const navigate = useNavigate()
  const [revision, setRevision] = useState(0)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const controllerRef = useRef(null)
  const creatingRef = useRef(false)
  const refresh = useCallback(() => setRevision((value) => value + 1), [])
  useEffect(() => () => controllerRef.current?.abort(), [])
  useEffect(() => { setError(''); setSidebarOpen(false) }, [roomId])
  useEffect(() => {
    if (!sidebarOpen) return
    const closeOnEscape = (event) => { if (event.key === 'Escape') setSidebarOpen(false) }
    window.addEventListener('keydown', closeOnEscape)
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [sidebarOpen])

  async function create() {
    if (creatingRef.current) return
    creatingRef.current = true
    const controller = new AbortController()
    controllerRef.current = controller
    setCreating(true); setError('')
    try {
      const room = await ai.createRoom('새 채팅', token, controller.signal)
      if (controller.signal.aborted) return
      navigate(`/chat/${encodeURIComponent(room.id)}`)
      refresh(); setSidebarOpen(false)
    } catch (reason) {
      if (!controller.signal.aborted) setError(featureError(reason, '채팅방 기능'))
    } finally {
      creatingRef.current = false
      if (!controller.signal.aborted) setCreating(false)
    }
  }

  return <div className="chat-page">
    {error && <div className="inline-error chat-notice" role="alert"><p>{error}</p><button className="text-button" onClick={() => setError('')}>닫기</button></div>}
    <div className="chat-workspace">
      <RoomSidebar token={token} roomId={roomId} revision={revision} onCreate={create} creating={creating} onSelect={() => setSidebarOpen(false)} open={sidebarOpen} />
      {sidebarOpen && <button className="sidebar-backdrop" aria-label="채팅방 목록 닫기" onClick={() => setSidebarOpen(false)} />}
      {roomId ? <Conversation key={roomId} roomId={roomId} token={token} onActivity={refresh} sidebarOpen={sidebarOpen} onToggleSidebar={() => setSidebarOpen((value) => !value)} /> :
        <section className="chat-welcome" aria-labelledby="chat-title"><button className="button secondary sidebar-toggle welcome-toggle" aria-controls="room-sidebar" aria-expanded={sidebarOpen} onClick={() => setSidebarOpen((value) => !value)}>채팅방 목록</button><h1 id="chat-title">챗봇</h1><p>채팅방을 선택하거나 새 채팅을 시작하세요.</p><button className="button" disabled={creating} onClick={create}>{creating ? '만드는 중…' : '새 채팅'}</button></section>}
    </div>
  </div>
}
