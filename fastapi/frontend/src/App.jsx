import { Link, NavLink, Outlet, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { RequireAuth, useAuth } from './auth/AuthContext'
import { Feedback } from './components/Feedback'
import { AuthPage } from './pages/AuthPage'
import { PostListPage } from './pages/PostListPage'
import { PostDetailPage } from './pages/PostDetailPage'
import { NewPostPage } from './pages/NewPostPage'
import { RagPage } from './pages/RagPage'
import { ChatPage } from './pages/ChatPage'

function BoardLayout() {
  return <><div className="board-navigation"><nav aria-label="게시판 메뉴"><NavLink to="/" end>전체 게시글</NavLink><NavLink to="/me/posts">내 게시글</NavLink></nav><Link className="button" to="/posts/new">글쓰기</Link></div><Outlet /></>
}

export default function App() {
  const auth = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const isChat = location.pathname === '/chat' || location.pathname.startsWith('/chat/')
  const isBoard = location.pathname === '/' || location.pathname.startsWith('/posts') || location.pathname === '/me/posts'

  function logout() {
    auth.logout()
    navigate('/')
  }

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">본문으로 이동</a>
      <header className="site-header">
        <div className="header-inner">
          <nav className="main-nav" aria-label="주 메뉴">
            <Link to="/" className={isBoard ? 'active' : ''} aria-current={isBoard ? 'page' : undefined}>게시판</Link>
            <NavLink to="/rag">RAG Agent</NavLink>
            <NavLink to="/chat">챗봇</NavLink>
          </nav>
          <div className="account-nav">
            {auth.user ? <><span className="account-email" title={auth.user.email}>{auth.user.email}</span><button className="text-button" onClick={logout}>로그아웃</button></> :
              <Link className="text-button" to="/login" state={{ from: location.pathname.startsWith('/login') || location.pathname === '/signup' ? '/' : location.pathname + location.search }}>로그인</Link>}
          </div>
        </div>
      </header>
      <main id="main" className={`main-container ${isChat && auth.user ? 'chat-container' : ''}`}>
        {auth.notice && <div className="notice" role="status"><span>{auth.notice}</span><button aria-label="알림 닫기" onClick={auth.clearNotice}>×</button></div>}
        <Routes>
          <Route element={<BoardLayout />}>
            <Route path="/" element={<PostListPage />} />
            <Route path="/me/posts" element={<RequireAuth><PostListPage mine /></RequireAuth>} />
            <Route path="/posts/new" element={<RequireAuth><NewPostPage /></RequireAuth>} />
            <Route path="/posts/:postId" element={<PostDetailPage />} />
          </Route>
          <Route path="/rag" element={<RequireAuth><RagPage key={auth.user?.id} /></RequireAuth>} />
          <Route path="/chat/:roomId?" element={<RequireAuth><ChatPage key={auth.user?.id} /></RequireAuth>} />
          <Route path="/login" element={<AuthPage />} />
          <Route path="/signup" element={<AuthPage signup />} />
          <Route path="*" element={<Feedback title="페이지를 찾을 수 없습니다."><Link to="/">게시판으로 돌아가기</Link></Feedback>} />
        </Routes>
      </main>
    </div>
  )
}
