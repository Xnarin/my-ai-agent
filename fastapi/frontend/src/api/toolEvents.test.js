import assert from 'node:assert/strict'
import { test } from 'node:test'
import { interruptToolCalls, updateToolCalls } from './toolEvents.js'

const first = { id: 'weather-1', name: 'search_weather', label: '날씨 조회' }
const second = { ...first, id: 'weather-2' }

test('같은 도구의 병렬 호출과 완료를 실행 ID로 구분한다', () => {
  let calls = updateToolCalls([], 'tool_start', first)
  calls = updateToolCalls(calls, 'tool_start', second)
  calls = updateToolCalls(calls, 'tool_end', second)
  assert.deepEqual(calls, [{ ...first, status: 'running' }, { ...second, status: 'completed' }])
  calls = updateToolCalls(calls, 'tool_error', first)
  assert.deepEqual(calls, [{ ...first, status: 'failed' }, { ...second, status: 'completed' }])
})

test('중복 시작 이벤트가 완료된 도구를 실행 중으로 되돌리지 않는다', () => {
  const calls = updateToolCalls([], 'tool_end', first)
  assert.deepEqual(updateToolCalls(calls, 'tool_start', first), calls)
})

test('연결이 끊겨도 완료 상태를 유지하고 실행 중이던 도구만 확인 대상으로 바꾼다', () => {
  let calls = updateToolCalls([], 'tool_start', first)
  calls = updateToolCalls(calls, 'tool_end', second)
  assert.deepEqual(interruptToolCalls(calls), [
    { ...first, status: 'interrupted' }, { ...second, status: 'completed' },
  ])
  assert.equal(calls[0].status, 'running')
})
