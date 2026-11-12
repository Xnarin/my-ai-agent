import React, { useCallback, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

const API_BASE_URL = (import.meta.env.VITE_API_URL?.trim() || "/api").replace(/\/+$/, "");

async function request(path, options) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, options);
  } catch {
    throw new Error("백엔드에 연결할 수 없습니다. 서버 실행 상태를 확인해 주세요.");
  }
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(
      typeof data?.detail === "string" ? data.detail :
        response.status === 422 ? "입력 내용을 확인해 주세요." :
          `요청에 실패했습니다. 서버 실행 상태를 확인해 주세요. (HTTP ${response.status})`
    );
  }
  if (data === null) {
    throw new Error("서버 응답을 확인할 수 없습니다.");
  }
  return data;
}

function HealthCheck() {
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function checkHealth() {
    setLoading(true);
    setError("");
    setStatus("");
    try {
      const data = await request("/health");
      setStatus(data.status);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section aria-labelledby="health-heading">
      <h2 id="health-heading">상태 확인</h2>
      <p className="description">백엔드와 데이터베이스의 연결 상태를 확인합니다.</p>
      <button type="button" onClick={checkHealth} disabled={loading}>
        {loading ? "확인 중…" : "상태 확인하기"}
      </button>
      <div role="status">
        {status && <p className="success">상태: {status}{status === "ok" && " · 백엔드와 데이터베이스 연결이 정상입니다."}</p>}
      </div>
      {error && <p className="error" role="alert">{error}</p>}
    </section>
  );
}

function Notes() {
  const [text, setText] = useState("");
  const [notes, setNotes] = useState(null);
  const [saveError, setSaveError] = useState("");
  const [listError, setListError] = useState("");
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadNotes = useCallback(async () => {
    setLoading(true);
    setListError("");
    try {
      setNotes(await request("/notes"));
    } catch (err) {
      setListError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadNotes();
  }, [loadNotes]);

  async function saveNote(event) {
    event.preventDefault();
    if (!text.trim() || saving || loading) return;
    setSaving(true);
    setSaveError("");
    setMessage("");
    try {
      await request("/notes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text.trim() }),
      });
      setText("");
      setMessage("노트를 저장했습니다.");
      await loadNotes();
    } catch (err) {
      setSaveError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <section aria-labelledby="notes-heading">
      <h2 id="notes-heading">노트 저장·조회</h2>
      <p className="description">텍스트를 저장하고 최근 노트 20개를 확인합니다. API 키 없이 사용할 수 있습니다.</p>
      <form onSubmit={saveNote}>
        <label htmlFor="note">노트 내용</label>
        <textarea id="note" value={text} onChange={(event) => setText(event.target.value)}
          placeholder="저장할 내용을 입력하세요." required maxLength={5000} disabled={saving} />
        <button type="submit" disabled={saving || loading || !text.trim()}>
          {saving ? "저장 중…" : "노트 저장하기"}
        </button>
      </form>
      <div role="status">{message && <p className="success">{message}</p>}</div>
      {saveError && <p className="error" role="alert">{saveError}</p>}
      <div className="list-heading">
        <h3>저장된 노트</h3>
        <button type="button" className="secondary" onClick={loadNotes} disabled={loading || saving}>
          {loading ? "불러오는 중…" : "목록 새로고침"}
        </button>
      </div>
      {listError && <p className="error" role="alert">{listError}</p>}
      <div aria-live="polite" aria-busy={loading}>
        {notes === null ? loading && <p className="description">노트 목록을 불러오는 중…</p> :
          notes.length === 0 ? <p>저장된 노트가 없습니다.</p> :
            <ul className="results">{notes.map((note) => <li key={note.id}>
              <small>노트 #{note.id}</small>
              <p className="result-text">{note.text}</p>
            </li>)}</ul>}
      </div>
    </section>
  );
}

function Search() {
  const [query, setQuery] = useState("");
  const [documents, setDocuments] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function search(event) {
    event.preventDefault();
    if (!query.trim() || loading) return;
    setLoading(true);
    setError("");
    setDocuments(null);
    try {
      const data = await request("/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query.trim() }),
      });
      setDocuments(data.documents);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section aria-labelledby="search-heading">
      <h2 id="search-heading">pgvector로 텍스트 검색하기</h2>
      <p className="description">ingest.py로 등록한 텍스트에서 검색어와 관련된 내용을 찾습니다. 저장한 노트는 검색 대상에 포함되지 않습니다.</p>
      <form onSubmit={search}>
        <label htmlFor="query">검색어</label>
        <textarea id="query" value={query} onChange={(e) => setQuery(e.target.value)}
          placeholder="컨테이너를 삭제해도 데이터를 유지하려면?" required maxLength={1000} disabled={loading} />
        <button type="submit" disabled={loading || !query.trim()}>{loading ? "검색 중…" : "검색하기"}</button>
      </form>
      {error && <p className="error" role="alert">{error}</p>}
      <div aria-live="polite" aria-busy={loading}>
        {documents !== null && <><h3>검색 결과</h3>
          {documents.length === 0 ? <p>검색된 텍스트가 없습니다.</p> :
            <ul className="results">{documents.map((document) => <li key={document.id}>
            <p className="result-text">{document.text}</p>
            </li>)}</ul>}
        </>}
      </div>
    </section>
  );
}

function App() {
  return (
    <main>
      <p className="eyebrow">Docker Practice</p>
      <h1>백엔드 API 실습</h1>
      <p className="intro">서버 상태를 확인하고, 노트를 저장하고, pgvector로 텍스트를 검색합니다.</p>
      <HealthCheck />
      <Notes />
      <Search />
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
