import { useState } from 'react'
import { safeUrl } from './Markdown.js'
export { Markdown } from './Markdown.js'

export function CopyButton({ text }) {
  const [notice, setNotice] = useState('')
  async function copy() {
    try { await navigator.clipboard.writeText(text); setNotice('복사됨') }
    catch { setNotice('복사하지 못했습니다') }
  }
  return <button type="button" className="text-button copy-button" onClick={copy} aria-label="답변 복사">{notice || '복사'}</button>
}

export function Sources({ sources }) {
  if (!Array.isArray(sources) || !sources.length) return null
  return (
    <details className="sources">
      <summary>참고한 출처 <span>{sources.length}</span></summary>
      <ul>{sources.map((source, index) => {
        const item = typeof source === 'string' ? { title: source } : source || {}
        const url = safeUrl(item.url)
        const title = item.title || item.source || `문서 ${index + 1}`
        return <li key={index}>
          <div>{item.id != null && <span>[{item.id}] </span>}{url ? <a href={url} target="_blank" rel="noopener noreferrer">{title} ↗</a> : <strong>{title}</strong>}
            {item.page_number != null && <span className="source-page">{item.page_number}쪽</span>}</div>
          {item.excerpt && <p>{item.excerpt}</p>}
        </li>
      })}</ul>
    </details>
  )
}

export function Composer({ value, onChange, onSubmit, pending, disabled, label = '메시지', placeholder, inputRef, hint }) {
  function keyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing && event.keyCode !== 229) {
      event.preventDefault()
      if (!pending && !disabled && value.trim()) onSubmit()
    }
  }
  return (
    <form className="composer" onSubmit={(event) => { event.preventDefault(); onSubmit() }}>
      <label className="sr-only" htmlFor="ai-input">{label}</label>
      <textarea id="ai-input" ref={inputRef} value={value} onChange={(event) => onChange(event.target.value)}
        onKeyDown={keyDown} placeholder={placeholder} rows={3} maxLength={10000} disabled={disabled || pending} required />
      <div className="composer-bottom"><span>{hint || 'Enter 전송 · Shift+Enter 줄바꿈'}</span>
        <button className="button" type="submit" disabled={disabled || pending || !value.trim()}>{pending ? '답변 생성 중…' : '보내기'}</button>
      </div>
    </form>
  )
}

export function Pending({ children = '답변을 준비하고 있어요' }) {
  return <div className="pending-status" role="status"><span className="pulse-dot" />{children}</div>
}

export function ToolActivity({ calls = [] }) {
  if (!calls.length) return null
  const statuses = { running: '조회 중', completed: '완료', failed: '실패', interrupted: '결과 확인 필요' }
  return <ul className="tool-activity" aria-label="도구 실행 현황" aria-live="polite">
    {calls.map((call) => <li key={call.id} className={`tool-activity-${call.status}`}>
      <span className="tool-activity-icon" aria-hidden="true">{call.status === 'running' ? <span className="pulse-dot" /> : call.status === 'completed' ? '✓' : '!'}</span>
      <span className="tool-activity-label">{call.label}</span>
      <span className="tool-activity-status">{statuses[call.status]}</span>
    </li>)}
  </ul>
}
