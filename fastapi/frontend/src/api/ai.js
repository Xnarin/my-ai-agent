import { ApiError, request } from './client.js'
import { streamRequest } from './stream.js'

const roomPath = (id) => `/chat/rooms/${encodeURIComponent(id)}`
const query = (values) => {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(values)) {
    if (value !== undefined && value !== null && value !== '') params.set(key, String(value))
  }
  return `?${params}`
}

function validateRoom(data) {
  if (!data || !['string', 'number'].includes(typeof data.id) || !String(data.id) || typeof data.title !== 'string') {
    throw new ApiError('채팅방 정보를 읽을 수 없습니다.', 0)
  }
  return data
}

export function validateTurn(data) {
  if (!data?.user_message?.id || !data?.assistant_message?.id ||
    data.user_message.role !== 'user' || data.assistant_message.role !== 'assistant' ||
    typeof data.user_message.content !== 'string' || typeof data.assistant_message.content !== 'string') {
    throw new ApiError('대화 응답을 읽을 수 없습니다. 대화 기록을 새로고침해 주세요.', 0)
  }
  return data
}

export function mergeMessages(current, incoming) {
  const messages = new Map(current.map((item) => [String(item.id), item]))
  for (const item of incoming) messages.set(String(item.id), item)
  return [...messages.values()]
}

export const ai = {
  ask: async (question, token, signal, onEvent) => {
    const data = await streamRequest('/chat/rag/stream', { body: { question }, token, signal, onEvent })
    if (typeof data?.answer !== 'string') throw new ApiError('답변을 읽을 수 없습니다.', 0)
    return data
  },
  rooms: async (params, token, signal) => {
    const data = await request(`/chat/rooms${query(params)}`, { token, signal })
    if (!Array.isArray(data?.items) || !Number.isInteger(data.total) || data.total < 0) throw new ApiError('채팅방 목록을 읽을 수 없습니다.', 0)
    data.items.forEach(validateRoom)
    return data
  },
  room: async (id, token, signal) => validateRoom(await request(roomPath(id), { token, signal })),
  createRoom: async (title, token, signal) => validateRoom(await request('/chat/rooms', { method: 'POST', body: { title }, token, signal })),
  renameRoom: async (id, title, token, signal) => validateRoom(await request(roomPath(id), { method: 'PATCH', body: { title }, token, signal })),
  deleteRoom: (id, token, signal) => request(roomPath(id), { method: 'DELETE', token, signal }),
  messages: async (id, cursor, token, signal) => {
    const data = await request(`${roomPath(id)}/messages${query({ cursor, limit: 30 })}`, { token, signal })
    if (!Array.isArray(data?.items) || typeof data.has_more !== 'boolean' || (data.has_more && !data.next_cursor)) {
      throw new ApiError('대화 기록을 읽을 수 없습니다.', 0)
    }
    if (data.items.some((item) => !item?.id || !['user', 'assistant'].includes(item.role) || typeof item.content !== 'string')) {
      throw new ApiError('메시지 형식을 확인할 수 없습니다.', 0)
    }
    return data
  },
  send: async (id, content, token, signal) => validateTurn(await request(`${roomPath(id)}/messages`, {
    method: 'POST', body: { content }, token, signal, timeoutMs: 120000,
  })),
  stream: async (id, content, token, signal, onEvent) => validateTurn(await streamRequest(`${roomPath(id)}/messages/stream`, {
    body: { content }, token, signal, onEvent,
  })),
}

export function featureError(error, label) {
  return [404, 405, 501].includes(error.status)
    ? `${label}가 아직 준비되지 않았습니다. 준비가 완료되면 다시 시도해 주세요.`
    : error.message
}
