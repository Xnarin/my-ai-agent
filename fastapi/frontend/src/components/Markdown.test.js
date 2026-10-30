import assert from 'node:assert/strict'
import { test } from 'node:test'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { Markdown, safeUrl } from './Markdown.js'

const render = (children) => renderToStaticMarkup(createElement(Markdown, { children }))

test('AI 답변의 HTML과 위험한 URL을 실행 가능한 요소로 만들지 않는다', () => {
  const html = render('<img src=x onerror=alert(1)>\n\n[실행](javascript:alert) [문서](https://example.com)')
  assert.ok(!html.includes('<img'))
  assert.ok(!html.includes('href="javascript:'))
  assert.ok(html.includes('&lt;img'))
  assert.ok(html.includes('href="https://example.com/"'))
  assert.equal(safeUrl('data:text/html,test'), undefined)
  assert.equal(safeUrl('//example.com'), undefined)
})

test('제목, 목록, 표, 강조, 인라인 코드와 코드 블록을 표시한다', () => {
  const html = render('## 요약\n\n**중요** `code`\n\n- 첫째\n- 둘째\n\n| 도시 | 날씨 |\n| --- | --- |\n| 서울 | 맑음 |\n\n```python\nprint("안녕")\n```')
  for (const text of ['<h3>요약</h3>', '<strong>중요</strong>', '<code>code</code>', '<ul>', '<table>', '<td>서울</td>', '<pre><code>']) assert.ok(html.includes(text))
})

test('스트리밍 중 아직 닫히지 않은 코드 블록도 표시한다', () => {
  assert.ok(render('```python\nprint(').includes('<pre><code>print(</code></pre>'))
})
