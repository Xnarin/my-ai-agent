import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ai, mergeMessages } from '../api/ai'
import { Composer, CopyButton, Markdown, Pending, Sources, ToolActivity } from './AIContent'
import { interruptToolCalls, toolEventNames, updateToolCalls } from '../api/toolEvents.js'
import { Feedback } from './Feedback'
import { RoomDialog } from './RoomDialog'

const suggestions = ['서울 날씨 알려 줘.', '현재 상영 중인 영화 3개 알려 줘.']

export function Conversation({ roomId, token, onActivity, onToggleSidebar, sidebarOpen }) {
  const navigate = useNavigate()
  const [room, setRoom] = useState(null)
  const [messages, setMessages] = useState([])
  const [page, setPage] = useState({ next_cursor: null, has_more: false })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [olderError, setOlderError] = useState('')
  const [olderLoading, setOlderLoading] = useState(false)
  const [revision, setRevision] = useState(0)
  const [draft, setDraft] = useState('')
  const [pending, setPending] = useState(false)
  const [sendError, setSendError] = useState('')
  const [progress, setProgress] = useState('')
  const [dialog, setDialog] = useState(null)
  const [showBottom, setShowBottom] = useState(false)
  const scrollRef = useRef(null)
  const inputRef = useRef(null)
  const stickRef = useRef(true)
  const anchorRef = useRef(null)
  const sendRef = useRef(null)
  const olderRef = useRef(null)
  const busyRef = useRef(false)

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true); setError(''); setOlderError('')
    olderRef.current?.abort(); setOlderLoading(false)
    Promise.all([ai.room(roomId, token, controller.signal), ai.messages(roomId, null, token, controller.signal)])
      .then(([roomData, history]) => {
        if (controller.signal.aborted) return
        stickRef.current = true
        anchorRef.current = null
        setRoom(roomData); setMessages(history.items); setPage(history); setSendError('')
      })
      .catch((reason) => { if (!controller.signal.aborted) setError(reason.message) })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [roomId, token, revision])

  useEffect(() => () => { sendRef.current?.abort(); olderRef.current?.abort() }, [])

  useLayoutEffect(() => {
    const element = scrollRef.current
    if (!element) return
    if (anchorRef.current) {
      element.scrollTop = anchorRef.current.top + element.scrollHeight - anchorRef.current.height
      anchorRef.current = null
    } else if (stickRef.current) element.scrollTop = element.scrollHeight
  }, [messages, loading, pending])

  async function older() {
    if (olderLoading || !page.has_more || pending) return
    const controller = new AbortController()
    olderRef.current = controller
    setOlderLoading(true); setOlderError('')
    try {
      const result = await ai.messages(roomId, page.next_cursor, token, controller.signal)
      if (controller.signal.aborted) return
      const element = scrollRef.current
      anchorRef.current = { top: element.scrollTop, height: element.scrollHeight }
      stickRef.current = false
      setMessages((current) => mergeMessages(result.items, current))
      setPage(result)
    } catch (reason) {
      if (!controller.signal.aborted) setOlderError(reason.message)
    } finally {
      if (!controller.signal.aborted) setOlderLoading(false)
    }
  }

  async function submit() {
    const content = draft.trim()
    if (!content || busyRef.current || loading || error || sendError || !room) return
    busyRef.current = true
    const controller = new AbortController()
    sendRef.current = controller
    const localId = crypto.randomUUID()
    const userId = `local-user-${localId}`
    const answerId = `local-answer-${localId}`
    stickRef.current = true; setShowBottom(false)
    setDraft(''); setPending(true); setSendError(''); setProgress('답변을 준비하고 있어요')
    setMessages((current) => [...current,
      { id: userId, role: 'user', content, status: 'pending' },
      { id: answerId, role: 'assistant', content: '', sources: [], tool_calls: [], status: 'pending' },
    ])
    try {
      const result = await ai.stream(roomId, content, token, controller.signal, (event, payload) => {
        if (controller.signal.aborted) return
        if (event === 'status' && typeof payload.message === 'string') setProgress(payload.message)
        if (event === 'token' && typeof payload.content === 'string') {
          setProgress('답변을 작성하고 있어요')
          setMessages((current) => current.map((item) => item.id === answerId ? { ...item, content: item.content + payload.content } : item))
        }
        if (event === 'sources' && Array.isArray(payload.sources)) {
          setMessages((current) => current.map((item) => item.id === answerId ? { ...item, sources: payload.sources } : item))
        }
        if (toolEventNames.includes(event)) {
          setProgress(event === 'tool_start' ? '도구로 정보를 확인하고 있어요' : '조회 결과를 확인하고 있어요')
          setMessages((current) => current.map((item) => item.id === answerId ? { ...item, tool_calls: updateToolCalls(item.tool_calls, event, payload) } : item))
        }
      })
      if (controller.signal.aborted) return
      setMessages((current) => current.map((item) => item.id === userId ? result.user_message : item.id === answerId ? { ...result.assistant_message, tool_calls: interruptToolCalls(item.tool_calls) } : item))
      onActivity()
    } catch (reason) {
      if (controller.signal.aborted) return
      setSendError(reason.message)
      setDraft(content)
      setMessages((current) => current.map((item) => item.id === answerId || item.id === userId ? { ...item, status: 'failed', tool_calls: interruptToolCalls(item.tool_calls) } : item))
    } finally {
      busyRef.current = false
      if (!controller.signal.aborted) { setPending(false); setProgress('') }
    }
  }

  function saved(updated) {
    if (dialog === 'delete') navigate('/chat', { replace: true })
    else setRoom(updated)
    setDialog(null); onActivity()
  }

  return <section className="conversation" aria-labelledby="conversation-title">
    <header className="conversation-header"><button className="button secondary sidebar-toggle" aria-controls="room-sidebar" aria-expanded={sidebarOpen} onClick={onToggleSidebar}>채팅방</button>
      <div className="conversation-title"><h1 id="conversation-title">{room?.title || '채팅방'}</h1></div>
      <div className="conversation-actions"><button className="text-button" onClick={() => setRevision((value) => value + 1)} disabled={pending || loading}>새로고침</button><button className="text-button" disabled={!room || pending || loading || Boolean(error)} onClick={() => setDialog('rename')}>제목 변경</button><button className="text-button danger-text" disabled={!room || pending || loading || Boolean(error)} onClick={() => setDialog('delete')}>삭제</button></div>
    </header>
    <div className="message-scroll" ref={scrollRef} onScroll={(event) => {
      const element = event.currentTarget
      stickRef.current = element.scrollHeight - element.scrollTop - element.clientHeight < 80
      setShowBottom(!stickRef.current)
    }}>
      {loading ? <Feedback loading /> : error ? <Feedback error={error} retry={() => setRevision((value) => value + 1)} /> : <div className="message-content">
        {page.has_more && <div className="older-control"><button className="button secondary" disabled={olderLoading || pending} onClick={older}>{olderLoading ? '불러오는 중…' : '이전 메시지 불러오기'}</button></div>}
        {olderError && <p className="form-error" role="alert">{olderError}</p>}
        {messages.length === 0 && <div className="conversation-empty"><h2>메시지를 입력해 대화를 시작하세요.</h2><div className="chat-suggestions">{suggestions.map((text) => <button key={text} onClick={() => { setDraft(text); inputRef.current?.focus() }}>{text}</button>)}</div></div>}
        {messages.map((message) => <article key={message.id} className={`message message-${message.role}`} aria-label={message.role === 'user' ? '내 메시지' : '챗봇 답변'}>
          <div className="message-meta"><strong>{message.role === 'user' ? '나' : 'AI 챗봇'}</strong>{message.role === 'assistant' && message.content && message.status !== 'pending' && <CopyButton text={message.content} />}</div>
          <div className="message-body">{message.role === 'user' ? <p>{message.content}</p> : <><ToolActivity calls={message.tool_calls} /><Markdown>{message.content}</Markdown><Sources sources={message.sources} /></>}
            {message.status === 'failed' && <p className="message-incomplete">{message.role === 'assistant' ? '완료되지 않은 답변' : '전송 결과 확인 필요'}</p>}
            {message.status === 'pending' && message.role === 'assistant' && !pending && <p className="message-incomplete">완료 상태를 확인하려면 대화 기록을 새로고침해 주세요.</p>}
          </div>
        </article>)}
        {pending && <Pending>{progress}</Pending>}
      </div>}
    </div>
    <div className="conversation-footer">
      {showBottom && <button className="latest-button" onClick={() => { stickRef.current = true; scrollRef.current.scrollTop = scrollRef.current.scrollHeight; setShowBottom(false) }}>최신 메시지로 ↓</button>}
      {sendError && <div className="inline-error" role="alert"><p>{sendError}</p><p>전송 결과를 확인하려면 대화 기록을 새로고침해 주세요.</p><button className="text-button" onClick={() => setRevision((value) => value + 1)} disabled={loading}>대화 기록 새로고침</button></div>}
      <Composer value={draft} onChange={setDraft} onSubmit={submit} pending={pending} disabled={loading || Boolean(error) || Boolean(sendError)} placeholder="메시지를 입력하세요" inputRef={inputRef} />
      <p className="chat-footnote">날씨·영화 정보는 실습용 데이터입니다.</p>
    </div>
    {dialog && <RoomDialog key={`${dialog}-${room.id}`} room={room} action={dialog} token={token} onClose={() => setDialog(null)} onSaved={saved} />}
  </section>
}
