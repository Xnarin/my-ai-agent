### 실행

백엔드는 `http://127.0.0.1:8000`에서 실행한다.

```bash
cd frontend
npm install
npm run dev
```

브라우저에서 `http://127.0.0.1:5173`에 접속한다.


### 연결 설정

`.env`에서 백엔드 주소를 설정한다.

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
```