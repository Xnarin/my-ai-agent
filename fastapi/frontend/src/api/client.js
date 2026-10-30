const env = import.meta.env || {}
export const API_BASE_URL = (env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')
export const TOKEN_KEY = 'access_token'
export const SESSION_EXPIRED_EVENT = 'moa:session-expired'

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export function unwrapResponse(body) {
  return body && typeof body === 'object' && !Array.isArray(body) && 'data' in body
    ? body.data
    : body
}

export function errorMessage(body, status) {
  const detail = body?.error?.message || body?.message || body?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((item) => {
      const field = item.loc?.filter((part) => part !== 'body').join('.')
      return [field, item.msg].filter(Boolean).join(': ')
    }).join('\n')
  }
  return ({
    401: '로그인이 필요하거나 로그인 시간이 만료되었습니다.',
    403: '이 작업을 할 권한이 없습니다.',
    404: '요청한 내용을 찾을 수 없습니다.',
    409: '이미 등록된 정보입니다.',
    422: '입력한 내용을 확인해 주세요.',
  })[status] || '요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.'
}

export function notifySessionExpired(status, token) {
  if (status === 401 && token && globalThis.sessionStorage?.getItem(TOKEN_KEY) === token) {
    window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT))
  }
}

export async function request(path, { method = 'GET', body, token, signal, timeoutMs = 15000 } = {}) {
  const controller = new AbortController()
  const abort = () => controller.abort()
  const timeout = setTimeout(abort, timeoutMs)
  signal?.addEventListener('abort', abort, { once: true })
  if (signal?.aborted) abort()

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      signal: controller.signal,
      headers: {
        Accept: 'application/json',
        ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
    })
    notifySessionExpired(response.status, token)
    const text = await response.text()
    let payload = null
    try {
      payload = text ? JSON.parse(text) : null
    } catch {
      throw new ApiError('서버 응답을 읽을 수 없습니다. API 주소를 확인해 주세요.', response.status)
    }
    if (!response.ok) {
      throw new ApiError(errorMessage(payload, response.status), response.status)
    }
    return unwrapResponse(payload)
  } catch (error) {
    if (signal?.aborted || error instanceof ApiError) throw error
    if (controller.signal.aborted) throw new ApiError('서버 응답이 늦어지고 있습니다. 다시 시도해 주세요.', 0)
    throw new ApiError('서버에 연결할 수 없습니다. 서버 실행 상태와 연결 설정을 확인해 주세요.', 0)
  } finally {
    clearTimeout(timeout)
    signal?.removeEventListener('abort', abort)
  }
}

// /posts와 /me/posts는 전체 배열을 반환하므로 화면에서 검색·정렬·페이지 분할을 처리한다.
export function normalizePosts(data, { search = '', order = 'desc', offset = 0, limit = 10 } = {}) {
  if (Array.isArray(data)) {
    const filtered = data
      .filter((post) => post.title.toLocaleLowerCase().includes(search.toLocaleLowerCase()))
      .sort((a, b) => order === 'asc' ? a.id - b.id : b.id - a.id)
    return { items: filtered.slice(offset, offset + limit), total: filtered.length }
  }
  throw new ApiError('게시글 목록 응답 형식을 확인해 주세요.', 0)
}

export const api = {
  login: (body) => request('/auth/login', { method: 'POST', body }),
  signup: (body) => request('/auth/signup', { method: 'POST', body }),
  me: (token, signal) => request('/me', { token, signal }),
  posts: async (params, token, signal) => {
    const path = token ? '/me/posts' : '/posts'
    return normalizePosts(await request(path, { token, signal }), params)
  },
  post: (id, signal) => request(`/posts/${id}`, { signal }),
  createPost: (body, token) => request('/posts', { method: 'POST', body, token }),
  comments: async (id, signal) => {
    const data = await request(`/posts/${id}/comments`, { signal })
    if (Array.isArray(data)) return data
    throw new ApiError('댓글 목록 응답 형식을 확인해 주세요.', 0)
  },
  createComment: (id, body, token) => request(`/posts/${id}/comments`, { method: 'POST', body, token }),
}
