import { API_BASE_URL, ApiError, errorMessage, notifySessionExpired } from './client.js'
import { toolEventNames } from './toolEvents.js'

// UTF-8 문자, 줄바꿈, 이벤트 경계가 서로 다른 청크에 나뉠 수 있다.
export async function consumeSSE(body, onEvent) {
  const reader = body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let event = 'message'
  let data = []

  function line(value) {
    if (value === '') {
      if (!data.length) { event = 'message'; return false }
      const current = { event, data: data.join('\n') }
      event = 'message'
      data = []
      return onEvent(current) === true
    }
    if (value.startsWith(':')) return false
    const colon = value.indexOf(':')
    const field = colon < 0 ? value : value.slice(0, colon)
    let content = colon < 0 ? '' : value.slice(colon + 1)
    if (content.startsWith(' ')) content = content.slice(1)
    if (field === 'event') event = content
    if (field === 'data') data.push(content)
    return false
  }

  try {
    while (true) {
      const { value, done } = await reader.read()
      buffer += decoder.decode(value, { stream: !done })
      let match
      while ((match = /[\r\n]/.exec(buffer))) {
        const index = match.index
        if (!done && buffer[index] === '\r' && index === buffer.length - 1) break
        const width = buffer[index] === '\r' && buffer[index + 1] === '\n' ? 2 : 1
        const content = buffer.slice(0, index)
        buffer = buffer.slice(index + width)
        if (line(content)) return
      }
      if (done) return
    }
  } finally {
    await reader.cancel().catch(() => {})
    reader.releaseLock()
  }
}

export async function streamRequest(path, { body, token, signal, onEvent, timeoutMs = 120000 } = {}) {
  const controller = new AbortController()
  const abort = () => controller.abort()
  const timer = setTimeout(abort, timeoutMs)
  signal?.addEventListener('abort', abort, { once: true })
  if (signal?.aborted) abort()
  let result

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream', Authorization: `Bearer ${token}` },
      body: JSON.stringify(body),
      signal: controller.signal,
    })
    notifySessionExpired(response.status, token)
    if (!response.ok) {
      const payload = await response.json().catch(() => null)
      throw new ApiError(errorMessage(payload, response.status), response.status)
    }
    if (!response.headers.get('content-type')?.includes('text/event-stream') || !response.body) {
      throw new ApiError('스트리밍 응답을 읽을 수 없습니다.', 0)
    }
    await consumeSSE(response.body, ({ event, data }) => {
      if (!['token', 'status', 'sources', 'done', 'error', ...toolEventNames].includes(event)) return false
      let payload
      try { payload = JSON.parse(data) }
      catch { throw new ApiError('답변 데이터의 형식을 확인할 수 없습니다.', 0) }
      if (!payload || typeof payload !== 'object' || Array.isArray(payload) ||
        (event === 'token' && typeof payload.content !== 'string') ||
        (event === 'status' && typeof payload.message !== 'string') ||
        (event === 'sources' && !Array.isArray(payload.sources)) ||
        (toolEventNames.includes(event) && ['id', 'name', 'label'].some((key) => typeof payload[key] !== 'string' || !payload[key].trim()))) {
        throw new ApiError('답변 데이터의 형식을 확인할 수 없습니다.', 0)
      }
      if (event === 'error') throw new ApiError(payload.message || '답변 생성 중 오류가 발생했습니다.', 0)
      onEvent?.(event, payload)
      if (event === 'done') { result = payload; return true }
      return false
    })
    if (!result) throw new ApiError('답변이 완료되기 전에 연결이 끊겼습니다.', 0)
    return result
  } catch (error) {
    if (signal?.aborted || error instanceof ApiError) throw error
    if (controller.signal.aborted) throw new ApiError('답변 생성 시간이 초과되었습니다.', 0)
    throw new ApiError('답변을 받는 중 연결이 끊겼습니다.', 0)
  } finally {
    clearTimeout(timer)
    signal?.removeEventListener('abort', abort)
  }
}
