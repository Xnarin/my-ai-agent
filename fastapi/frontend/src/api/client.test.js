import assert from 'node:assert/strict'
import { test } from 'node:test'
import { api, ApiError, errorMessage, normalizePosts, request, SESSION_EXPIRED_EVENT, unwrapResponse } from './client.js'

test('일반 응답과 공통 data 응답에서 실제 데이터를 읽는다', () => {
  assert.deepEqual(unwrapResponse({ data: { id: 1 }, message: 'ok' }), { id: 1 })
  assert.deepEqual(unwrapResponse([{ id: 1 }]), [{ id: 1 }])
  assert.equal(unwrapResponse(null), null)
})

test('배열 목록은 검색 후 정렬하고 페이지를 나눈다', () => {
  const posts = [{ id: 1, title: 'React 질문' }, { id: 2, title: 'Python 질문' }, { id: 3, title: 'react 후기' }]
  assert.deepEqual(normalizePosts(posts, { search: 'REACT', offset: 1, limit: 1 }), { items: [posts[0]], total: 2 })
  assert.deepEqual(posts.map((post) => post.id), [1, 2, 3])
  assert.equal(normalizePosts(posts, { order: 'asc', limit: 1 }).items[0].id, 1)
  assert.deepEqual(normalizePosts(posts, { search: '없는 글' }), { items: [], total: 0 })
})

test('게시글 목록이 배열이 아니면 오류를 표시한다', () => {
  assert.throws(() => normalizePosts({ unexpected: [] }), ApiError)
})

test('FastAPI 검증 오류와 공통 오류 메시지를 표시한다', () => {
  assert.equal(errorMessage({ detail: [{ loc: ['body', 'title'], msg: '필수 입력' }] }, 422), 'title: 필수 입력')
  assert.equal(errorMessage({ error: { message: '권한이 없습니다.' } }, 403), '권한이 없습니다.')
  assert.equal(errorMessage({ detail: '로그인 실패' }, 401), '로그인 실패')
})

test('JSON 본문과 Bearer 토큰을 전달하고 data 응답을 읽는다', async (context) => {
  context.mock.method(globalThis, 'fetch', async (url, options) => {
    assert.equal(url, 'http://127.0.0.1:8000/posts')
    assert.equal(options.method, 'POST')
    assert.equal(options.headers.Authorization, 'Bearer test-token')
    assert.equal(options.headers['Content-Type'], 'application/json')
    assert.deepEqual(JSON.parse(options.body), { title: '제목', content: '내용' })
    return Response.json({ data: { id: 1 } }, { status: 201 })
  })
  assert.deepEqual(await request('/posts', { method: 'POST', body: { title: '제목', content: '내용' }, token: 'test-token' }), { id: 1 })
})

test('공개 요청에는 인증 헤더를 보내지 않고 빈 응답을 처리한다', async (context) => {
  context.mock.method(globalThis, 'fetch', async (_, options) => {
    assert.equal(options.headers.Authorization, undefined)
    assert.equal(options.headers['Content-Type'], undefined)
    return new Response(null, { status: 204 })
  })
  assert.equal(await request('/posts'), null)
})

test('게시글과 댓글 API의 경로·인증·공통 응답을 처리한다', async (context) => {
  const calls = []
  context.mock.method(globalThis, 'fetch', async (url, options) => {
    calls.push({ url, options })
    return Response.json({ data: options.method === 'POST' ? { id: 1 } : [] })
  })
  assert.deepEqual(await api.posts({ offset: 0, limit: 10, search: '', order: 'desc' }, 'test-token'), { items: [], total: 0 })
  assert.deepEqual(await api.createPost({ title: '제목', content: '본문' }, 'test-token'), { id: 1 })
  assert.deepEqual(await api.comments(42), [])
  assert.deepEqual(await api.createComment(42, { content: '댓글' }, 'test-token'), { id: 1 })
  await api.posts({ search: '제목', order: 'asc', offset: 10, limit: 10 })
  assert.equal(calls[0].url, 'http://127.0.0.1:8000/me/posts')
  assert.equal(calls[0].options.headers.Authorization, 'Bearer test-token')
  assert.equal(calls[1].url, 'http://127.0.0.1:8000/posts')
  assert.equal(calls[1].options.method, 'POST')
  assert.equal(calls[2].url, 'http://127.0.0.1:8000/posts/42/comments')
  assert.equal(calls[2].options.headers.Authorization, undefined)
  assert.equal(calls[3].url, 'http://127.0.0.1:8000/posts/42/comments')
  assert.equal(calls[3].options.method, 'POST')
  assert.equal(calls[3].options.headers.Authorization, 'Bearer test-token')
  assert.deepEqual(JSON.parse(calls[3].options.body), { content: '댓글' })
  assert.equal(calls[4].url, 'http://127.0.0.1:8000/posts')
  assert.equal(calls[4].options.headers.Authorization, undefined)
})

test('현재 세션의 401만 로그인 만료를 알린다', async (context) => {
  const events = []
  const previousWindow = globalThis.window
  const previousStorage = Object.getOwnPropertyDescriptor(globalThis, 'sessionStorage')
  globalThis.window = { dispatchEvent: (event) => events.push(event.type) }
  Object.defineProperty(globalThis, 'sessionStorage', { configurable: true, value: { getItem: () => 'current-token' } })
  context.after(() => {
    if (previousWindow === undefined) delete globalThis.window
    else globalThis.window = previousWindow
    if (previousStorage) Object.defineProperty(globalThis, 'sessionStorage', previousStorage)
    else delete globalThis.sessionStorage
  })
  context.mock.method(globalThis, 'fetch', async () => Response.json({ detail: '로그인 만료' }, { status: 401 }))
  await assert.rejects(request('/me', { token: 'old-token' }), { status: 401 })
  await assert.rejects(request('/auth/login', { method: 'POST' }), { status: 401 })
  assert.deepEqual(events, [])
  await assert.rejects(request('/me', { token: 'current-token' }), { status: 401 })
  assert.deepEqual(events, [SESSION_EXPIRED_EVENT])
})

test('네트워크 오류와 잘못된 JSON 응답을 처리한다', async (context) => {
  const mock = context.mock.method(globalThis, 'fetch', async () => { throw new TypeError('Failed to fetch') })
  await assert.rejects(request('/posts'), { name: 'ApiError', status: 0 })
  mock.mock.mockImplementation(async () => new Response('<html>Not an API</html>'))
  await assert.rejects(request('/posts'), /API 주소/)
})

test('화면 이동으로 취소한 요청은 연결 오류로 바꾸지 않는다', async (context) => {
  const controller = new AbortController()
  controller.abort()
  context.mock.method(globalThis, 'fetch', async (_, options) => {
    assert.equal(options.signal.aborted, true)
    throw new DOMException('Aborted', 'AbortError')
  })
  await assert.rejects(request('/posts', { signal: controller.signal }), { name: 'AbortError' })
})
