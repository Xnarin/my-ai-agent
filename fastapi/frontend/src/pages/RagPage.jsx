import { useEffect, useRef, useState } from 'react'
import { useAuth } from '../auth/AuthContext'
import { ai, featureError } from '../api/ai'
import { Composer, CopyButton, Markdown, Pending, Sources } from '../components/AIContent'

const suggestions = ['문서에서 다루는 주요 AI 산업 동향을 요약해 줘.', '생성형 AI의 주요 활용 사례를 알려 줘.', '문서에 나온 AI 정책 변화를 정리해 줘.']

export function RagPage() {
  const { token } = useAuth()
  const [question, setQuestion] = useState('')
  const [submitted, setSubmitted] = useState('')
  const [answer, setAnswer] = useState(null)
  const [pending, setPending] = useState(false)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const requestRef = useRef(null)
  const busyRef = useRef(false)
  const inputRef = useRef(null)
  useEffect(() => () => requestRef.current?.abort(), [])

  async function submit() {
    if (busyRef.current || !question.trim()) return
    busyRef.current = true
    const controller = new AbortController()
    requestRef.current = controller
    const started = performance.now()
    setPending(true)
    setError('')
    setAnswer({ answer: '', sources: [] })
    setStatus('문서를 검색하고 있어요')
    setSubmitted(question.trim())
    try {
      const result = await ai.ask(question.trim(), token, controller.signal, (event, data) => {
        if (controller.signal.aborted) return
        if (event === 'status') setStatus(data.message)
        if (event === 'sources') setAnswer(current => ({ ...current, sources: data.sources }))
        if (event === 'token') setAnswer(current => ({ ...current, answer: current.answer + data.content }))
      })
      if (!controller.signal.aborted) setAnswer({ ...result, elapsed_ms: result.elapsed_ms ?? performance.now() - started })
    } catch (reason) {
      if (!controller.signal.aborted) setError(featureError(reason, 'RAG Agent'))
    } finally {
      busyRef.current = false
      if (!controller.signal.aborted) setPending(false)
    }
  }

  function reset() {
    setQuestion(''); setSubmitted(''); setAnswer(null); setError(''); setStatus('')
    inputRef.current?.focus()
  }

  return (
    <section className="rag-page" aria-labelledby="rag-title">
      <div className="ai-heading"><h1 id="rag-title">RAG Agent</h1>
        {submitted && <button className="button secondary" disabled={pending} onClick={reset}>새 질문</button>}</div>
      <div className="rag-question"><p className="muted">각 질문은 독립적으로 처리됩니다. 필요한 맥락을 질문에 함께 적어 주세요.</p>
        <Composer value={question} onChange={setQuestion} onSubmit={submit} pending={pending} label="문서에 질문하기" placeholder="문서에 대해 질문하세요" inputRef={inputRef} />
      </div>
      {!submitted && <div className="suggestion-section"><p className="small-label">질문 예시</p><div className="suggestion-list">{suggestions.map((item) => <button key={item} onClick={() => { setQuestion(item); inputRef.current?.focus() }}>{item}</button>)}</div></div>}
      {submitted && <section className="rag-answer" aria-label="질문 결과">
        <div className="answer-heading"><h2>답변</h2>{answer?.answer && <div className="answer-tools">{Number.isFinite(answer.elapsed_ms) && <span>{(answer.elapsed_ms / 1000).toFixed(1)}초</span>}<CopyButton text={answer.answer} /></div>}</div>
        <p className="submitted-question">{submitted}</p>
        {pending && <Pending>{status}</Pending>}
        {error && <div className="inline-error" role="alert"><p>{error}</p><button className="text-button" onClick={submit}>다시 시도</button></div>}
        {answer && <><Markdown>{answer.answer}</Markdown><Sources sources={answer.sources} /></>}
      </section>}
    </section>
  )
}
