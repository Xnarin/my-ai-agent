import assert from 'node:assert/strict'
import { test } from 'node:test'
import { ai, mergeMessages, validateTurn } from './ai.js'
import { consumeSSE, streamRequest } from './stream.js'

const turn = {
  user_message: { id: 31, role: 'user', content: '서울 날씨', status: 'completed' },
  assistant_message: { id: 32, role: 'assistant', content: '서울은 맑습니다.', status: 'completed', sources: [] },
}
function stream(text, byteSize = 1) {
  const bytes = new TextEncoder().encode(text)
  return new ReadableStream({ start(controller) {
    for (let offset = 0; offset < bytes.length; offset += byteSize) controller.enqueue(bytes.slice(offset, offset + byteSize))
    controller.close()
  } })
}
function sse(text) { return new Response(stream(text), { headers: { 'Content-Type': 'text/event-stream; charset=utf-8' } }) }

test('SSE의 한글 UTF-8, CRLF, 여러 data 줄이 한 바이트씩 나뉘어도 이벤트를 복원한다', async () => {
  const events = []
  await consumeSSE(stream(': heartbeat\r\nevent: token\r\ndata: {"content":\r\ndata: "서울☀️"}\r\n\r\nevent: done\ndata: {}\n\n'), (event) => { events.push(event) })
  assert.deepEqual(events, [{ event: 'token', data: '{"content":\n"서울☀️"}' }, { event: 'done', data: '{}' }])
})

test('SSE 빈 data 필드, CR 줄바꿈과 미완성 이벤트를 처리한다', async () => {
  const events = []
  await consumeSSE(stream('event: token\rdata\r\revent: token\rdata: unfinished'), (event) => { events.push(event) })
  assert.deepEqual(events, [{ event: 'token', data: '' }])
})

test('인증된 POST 스트리밍은 새 메시지만 보내고 완료 이벤트에서 수신을 끝낸다', async (context) => {
  const events = []
  context.mock.method(globalThis, 'fetch', async (url, options) => {
    assert.equal(url, 'http://127.0.0.1:8000/chat/rooms/42/messages/stream')
    assert.equal(options.method, 'POST')
    assert.equal(options.headers.Authorization, 'Bearer token')
    assert.deepEqual(JSON.parse(options.body), { content: '서울 날씨' })
    return sse(`event: token\ndata: {"content":"서울"}\n\nevent: done\ndata: ${JSON.stringify(turn)}\n\nevent: error\ndata: {"message":"완료 후 무시"}\n\n`)
  })
  assert.deepEqual(await ai.stream(42, '서울 날씨', 'token', undefined, (event) => events.push(event)), turn)
  assert.deepEqual(events, ['token', 'done'])
})

test('완료 없이 연결이 닫히면 부분 답변 이후에도 실패로 처리한다', async (context) => {
  let partial = ''
  context.mock.method(globalThis, 'fetch', async () => sse('event: token\ndata: {"content":"부분 답변"}\n\n'))
  await assert.rejects(streamRequest('/chat', { token: 't', body: {}, onEvent: (_, data) => { partial += data.content } }), /완료되기 전에/)
  assert.equal(partial, '부분 답변')
})

test('도구 시작과 종료 이벤트를 최종 답변까지 순서대로 전달한다', async (context) => {
  const tool = { id: 'weather-run', name: 'search_weather', label: '날씨 조회' }
  const expected = [['tool_start', tool], ['tool_end', tool], ['token', { content: '서울은 맑습니다.' }], ['done', turn]]
  const events = []
  context.mock.method(globalThis, 'fetch', async () => sse(expected.map(([event, data]) => `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`).join('')))
  assert.deepEqual(await ai.stream(42, '서울 날씨', 'token', undefined, (event, payload) => events.push([event, payload])), turn)
  assert.deepEqual(events, expected)
})

test('도구 오류가 나도 Agent가 복구해 최종 답변을 보낼 수 있다', async (context) => {
  const tool = { id: 'weather-run', name: 'search_weather', label: '날씨 조회' }
  const events = []
  context.mock.method(globalThis, 'fetch', async () => sse(`event: tool_start\ndata: ${JSON.stringify(tool)}\n\nevent: tool_error\ndata: ${JSON.stringify(tool)}\n\nevent: done\ndata: ${JSON.stringify(turn)}\n\n`))
  assert.deepEqual(await ai.stream(42, '서울 날씨', 'token', undefined, (event) => events.push(event)), turn)
  assert.deepEqual(events, ['tool_start', 'tool_error', 'done'])
})

test('필수 정보가 없는 도구 이벤트는 거부한다', async (context) => {
  const fetch = context.mock.method(globalThis, 'fetch', async () => sse(''))
  for (const tool of [{ name: 'search_weather', label: '날씨 조회' }, { id: 'run', name: 'search_weather', label: '' }]) {
    fetch.mock.mockImplementation(async () => sse(`event: tool_start\ndata: ${JSON.stringify(tool)}\n\n`))
    await assert.rejects(ai.stream(42, '서울 날씨', 'token'), /데이터의 형식/)
  }
})

test('스트리밍 시작 전 HTTP 오류와 시작 후 실패 이벤트를 구분한다', async (context) => {
  const fetch = context.mock.method(globalThis, 'fetch', async () => Response.json({ error: { message: '접근 불가' } }, { status: 403 }))
  await assert.rejects(streamRequest('/chat', { token: 't' }), { status: 403, message: '접근 불가' })
  fetch.mock.mockImplementation(async () => sse('event: error\ndata: {"message":"생성 실패"}\n\n'))
  await assert.rejects(streamRequest('/chat', { token: 't' }), { status: 0, message: '생성 실패' })
})

test('잘못된 스트리밍 형식과 불완전한 최종 메시지를 거부한다', async (context) => {
  const fetch = context.mock.method(globalThis, 'fetch', async () => Response.json({ data: turn }))
  await assert.rejects(streamRequest('/chat', { token: 't' }), /스트리밍 응답/)
  fetch.mock.mockImplementation(async () => sse('event: token\ndata: not-json\n\n'))
  await assert.rejects(streamRequest('/chat', { token: 't' }), /데이터의 형식/)
  assert.throws(() => validateTurn({ answer: 'saved?' }), /대화 기록/)
})

test('스트리밍 취소와 타임아웃을 구분한다', async (context) => {
  context.mock.method(globalThis, 'fetch', async (_, { signal }) => new Promise((resolve, reject) => {
    if (signal.aborted) reject(new DOMException('Aborted', 'AbortError'))
    else signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')), { once: true })
  }))
  const controller = new AbortController()
  controller.abort()
  await assert.rejects(streamRequest('/chat', { token: 't', signal: controller.signal }), { name: 'AbortError' })
  await assert.rejects(streamRequest('/chat', { token: 't', timeoutMs: 5 }), /시간이 초과/)
})

test('채팅방 검색, 커서 조회, 제목 수정과 삭제의 API 계약을 유지한다', async (context) => {
  const calls = []
  context.mock.method(globalThis, 'fetch', async (url, options) => {
    calls.push({ url: new URL(url), ...options })
    if (url.includes('/messages?')) return Response.json({ data: { items: [], next_cursor: null, has_more: false } })
    if (options.method === 'DELETE') return new Response(null, { status: 204 })
    if (options.method === 'PATCH') return Response.json({ data: { id: 42, title: '새 제목' } })
    return Response.json({ data: { items: [], total: 0 } })
  })
  await ai.rooms({ search: '영화 & 날씨', order: 'desc', offset: 20, limit: 20 }, 'token')
  await ai.messages(42, 'abc+/=', 'token')
  await ai.renameRoom(42, '새 제목', 'token')
  await ai.deleteRoom(42, 'token')
  assert.equal(calls[0].url.searchParams.get('search'), '영화 & 날씨')
  assert.equal(calls[0].url.searchParams.get('offset'), '20')
  assert.equal(calls[1].url.searchParams.get('cursor'), 'abc+/=')
  assert.equal(calls[2].method, 'PATCH')
  assert.deepEqual(JSON.parse(calls[2].body), { title: '새 제목' })
  assert.equal(calls[3].method, 'DELETE')
  assert.ok(calls.every((call) => call.headers.Authorization === 'Bearer token'))
})

test('이전 대화 페이지의 중복 메시지는 한 번만 표시하고 최신 값을 유지한다', () => {
  assert.deepEqual(mergeMessages([{ id: 1, content: '이전' }, { id: 2, content: '중복' }], [{ id: '2', content: '최신' }, { id: 3, content: '다음' }]),
    [{ id: 1, content: '이전' }, { id: '2', content: '최신' }, { id: 3, content: '다음' }])
})

test('RAG는 인증된 SSE로 질문을 보내고 답변 조각·출처·최종 결과를 받는다', async (context) => {
  const result = { answer: '문서\n요약', sources: [{ id: 1, source: '문서.pdf', page_number: 3 }], elapsed_ms: 1300 }
  const events = []
  context.mock.method(globalThis, 'fetch', async (url, options) => {
    assert.equal(url, 'http://127.0.0.1:8000/chat/rag/stream')
    assert.equal(options.method, 'POST')
    assert.equal(options.headers.Authorization, 'Bearer token')
    assert.equal(options.headers.Accept, 'text/event-stream')
    assert.deepEqual(JSON.parse(options.body), { question: '문서 요약해 줘' })
    return sse([
      ['status', { message: '검색 중' }],
      ['sources', { sources: result.sources }],
      ['token', { content: '문서\n' }],
      ['token', { content: '요약' }],
      ['done', result],
    ].map(([event, data]) => `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`).join(''))
  })
  assert.deepEqual(await ai.ask('문서 요약해 줘', 'token', undefined, (event, data) => events.push({ event, data })), result)
  assert.deepEqual(events.map(item => item.event), ['status', 'sources', 'token', 'token', 'done'])
  assert.equal(events.filter(item => item.event === 'token').map(item => item.data.content).join(''), result.answer)
})

test('RAG 생성 오류는 받은 답변 조각을 유지하고 실패로 전달한다', async (context) => {
  let partial = ''
  context.mock.method(globalThis, 'fetch', async () => sse('event: token\ndata: {"content":"부분 답변"}\n\nevent: error\ndata: {"message":"생성 실패"}\n\n'))
  await assert.rejects(ai.ask('질문', 'token', undefined, (event, data) => {
    if (event === 'token') partial += data.content
  }), /생성 실패/)
  assert.equal(partial, '부분 답변')
})
