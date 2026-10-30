export const toolEventNames = ['tool_start', 'tool_end', 'tool_error']

export function updateToolCalls(calls = [], event, payload) {
  const status = { tool_start: 'running', tool_end: 'completed', tool_error: 'failed' }[event]
  if (!status) return calls
  const existing = calls.find((call) => call.id === payload.id)
  if (existing && event === 'tool_start') return calls
  const next = { id: payload.id, name: payload.name, label: payload.label, status }
  return existing ? calls.map((call) => call.id === payload.id ? next : call) : [...calls, next]
}

export function interruptToolCalls(calls = []) {
  return calls.map((call) => call.status === 'running' ? { ...call, status: 'interrupted' } : call)
}
