import { createElement as h } from 'react'

export function safeUrl(value) {
  if (typeof value !== 'string') return undefined
  try {
    const url = new URL(value)
    return ['http:', 'https:'].includes(url.protocol) ? url.href : undefined
  } catch { return undefined }
}

function inline(text) {
  const pattern = /(`[^`\n]+`|\*\*[^*\n]+\*\*|\*[^*\n]+\*|\[[^\]\n]+\]\([^\s)]+\))/g
  const parts = []
  let previous = 0
  for (const match of text.matchAll(pattern)) {
    if (match.index > previous) parts.push(text.slice(previous, match.index))
    const value = match[0]
    const key = match.index
    if (value.startsWith('`')) parts.push(h('code', { key }, value.slice(1, -1)))
    else if (value.startsWith('**')) parts.push(h('strong', { key }, value.slice(2, -2)))
    else if (value.startsWith('*')) parts.push(h('em', { key }, value.slice(1, -1)))
    else {
      const [, label, target] = /^\[([^\]]+)\]\((.+)\)$/.exec(value)
      const href = safeUrl(target)
      parts.push(h(href ? 'a' : 'span', href ? { key, href, target: '_blank', rel: 'noopener noreferrer' } : { key }, label))
    }
    previous = match.index + value.length
  }
  if (previous < text.length) parts.push(text.slice(previous))
  return parts
}

const cells = (line) => line.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map((cell) => cell.trim())
const tableDivider = (line) => line?.includes('|') && cells(line).every((cell) => /^:?-{3,}:?$/.test(cell))
const blockStart = (line) => /^(?:\s*$|\s*```|\s*~~~|#{1,6}\s|[-*+]\s|\d+\.\s|>\s?)/.test(line)

// HTML을 실행하지 않고 제목, 목록, 표, 코드 블록과 기본 인라인 서식을 표시한다.
export function Markdown({ children = '' }) {
  const lines = String(children).replace(/\r\n?/g, '\n').split('\n')
  const blocks = []
  let index = 0
  while (index < lines.length) {
    const line = lines[index]
    const key = index
    if (!line.trim()) { index++; continue }
    const fence = /^\s*(`{3,}|~{3,})(.*)$/.exec(line)
    if (fence) {
      const code = []
      index++
      while (index < lines.length && !lines[index].trim().startsWith(fence[1])) code.push(lines[index++])
      if (index < lines.length) index++
      blocks.push(h('pre', { key }, h('code', null, code.join('\n'))))
      continue
    }
    const heading = /^(#{1,6})\s+(.+)$/.exec(line)
    if (heading) { blocks.push(h(`h${Math.min(heading[1].length + 1, 6)}`, { key }, inline(heading[2]))); index++; continue }
    if (line.includes('|') && tableDivider(lines[index + 1])) {
      const headers = cells(line)
      const rows = []
      index += 2
      while (index < lines.length && lines[index].includes('|') && lines[index].trim()) {
        rows.push(h('tr', { key: index }, cells(lines[index++]).map((cell, cellIndex) => h('td', { key: cellIndex }, inline(cell)))))
      }
      blocks.push(h('table', { key }, h('thead', null, h('tr', null, headers.map((cell, cellIndex) => h('th', { key: cellIndex }, inline(cell))))), h('tbody', null, rows)))
      continue
    }
    const list = /^([-*+]|\d+\.)\s+/.exec(line)
    if (list) {
      const ordered = /\d/.test(list[1])
      const pattern = ordered ? /^\d+\.\s+/ : /^[-*+]\s+/
      const items = []
      while (index < lines.length && pattern.test(lines[index])) {
        items.push(h('li', { key: index }, inline(lines[index++].replace(pattern, ''))))
      }
      blocks.push(h(ordered ? 'ol' : 'ul', { key }, items))
      continue
    }
    if (/^>\s?/.test(line)) {
      const quote = []
      while (index < lines.length && /^>\s?/.test(lines[index])) quote.push(lines[index++].replace(/^>\s?/, ''))
      blocks.push(h('blockquote', { key }, inline(quote.join('\n'))))
      continue
    }
    const paragraph = [line]
    index++
    while (index < lines.length && !blockStart(lines[index]) && !tableDivider(lines[index + 1])) paragraph.push(lines[index++])
    blocks.push(h('p', { key }, inline(paragraph.join('\n'))))
  }
  return h('div', { className: 'markdown-content' }, blocks)
}
