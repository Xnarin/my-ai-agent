import { useEffect, useRef, useState } from 'react'
import { ai } from '../api/ai'

export function RoomDialog({ room, action, token, onClose, onSaved }) {
  const dialogRef = useRef(null)
  const controllerRef = useRef(null)
  const [title, setTitle] = useState(room.title)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState('')
  const deleting = action === 'delete'
  useEffect(() => {
    const dialog = dialogRef.current
    dialog.showModal()
    return () => { controllerRef.current?.abort(); dialog.close() }
  }, [])

  async function submit(event) {
    event.preventDefault()
    if (pending || (!deleting && !title.trim())) return
    const controller = new AbortController()
    controllerRef.current = controller
    setPending(true); setError('')
    try {
      const updated = deleting ? await ai.deleteRoom(room.id, token, controller.signal) : await ai.renameRoom(room.id, title.trim(), token, controller.signal)
      if (!controller.signal.aborted) onSaved(updated)
    } catch (reason) {
      if (!controller.signal.aborted) { setError(reason.message); setPending(false) }
    }
  }

  return <dialog ref={dialogRef} className="room-dialog" aria-labelledby="dialog-title" onCancel={(event) => { event.preventDefault(); if (!pending) onClose() }}>
    <form onSubmit={submit}><h2 id="dialog-title">{deleting ? '채팅방을 삭제할까요?' : '채팅방 제목 변경'}</h2>
      {deleting ? <p>“{room.title}”의 대화가 삭제됩니다. 삭제한 대화는 되돌릴 수 없습니다.</p> : <label className="dialog-field">제목<input autoFocus value={title} onChange={(event) => setTitle(event.target.value)} maxLength={100} required disabled={pending} /></label>}
      {error && <p className="form-error" role="alert">{error}</p>}
      <div className="form-actions"><button type="button" className="button secondary" onClick={onClose} disabled={pending} autoFocus={deleting}>취소</button><button className={`button ${deleting ? 'danger' : ''}`} disabled={pending || (!deleting && !title.trim())}>{pending ? '처리 중…' : deleting ? '삭제' : '저장'}</button></div>
    </form>
  </dialog>
}
