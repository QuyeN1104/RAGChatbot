# Lumen Chat UI

Frontend React/TypeScript của hệ thống RAG Chatbot. Repository đã có Docker Compose để khởi chạy đồng thời FastAPI và UI, vì vậy Docker là luồng chạy mặc định.

## Chạy toàn bộ dự án bằng Docker Compose

Từ thư mục gốc repository:

```bash
cp .env.example .env
docker compose up --build
```

Sau khi các container khởi động:

- UI: `http://localhost:3000`
- API: `http://localhost:8000`
- Dữ liệu persistent: `./data`
- UI Nginx chuyển tiếp các request `/api/*` tới FastAPI.

Dừng hệ thống:

```bash
docker compose down
```

Nếu dùng Ollama, cần khởi động Ollama trên host và pull model đã cấu hình trong `.env`. Service API dùng host networking để truy cập Ollama tại `localhost:11434`.

## Chạy frontend riêng khi phát triển

Chỉ dùng cách này khi đang chỉnh sửa UI và muốn hot reload:

```bash
cd ui
npm install
npm run dev
```

Vite chạy tại `http://localhost:5173` và proxy `/api` tới `http://localhost:8000`. Khi đó backend cần được chạy riêng hoặc qua Docker:

```bash
docker compose up --build api
```

Tạo và kiểm tra production bundle:

```bash
cd ui
./node_modules/.bin/tsc --noEmit
npm run build
npm run preview
```

## Cấu trúc frontend

```text
src/
├── components/          # Sidebar, navbar, message, composer và UI nhỏ
├── context/             # ChatContext, localStorage và logic giao diện
├── data/                # Hội thoại mẫu, model và gợi ý
├── App.tsx
├── main.tsx
├── styles.css           # Tailwind + design tokens + responsive CSS
├── types.ts
└── utils.ts
```

## Tương tác giao diện

- Tạo, chọn, tìm kiếm, đổi tên và xóa cuộc trò chuyện.
- Gửi bằng Enter; Shift + Enter xuống dòng; dừng/tạo lại/chỉnh sửa phản hồi.
- Kéo thả hoặc chọn PDF, upload vào vector store và xem trạng thái xử lý.
- Render Markdown, bảng, trích dẫn và code block có nút sao chép.
- Chuyển light/dark mode, thu gọn sidebar và dùng drawer trên mobile.
- Lưu trạng thái giao diện trong localStorage.

Frontend sử dụng trực tiếp các endpoint `/api/health`, `/api/models`, `/api/chat`, `/api/upload`, `/api/documents` và `/api/sessions`. Tên tùy chỉnh của session được giữ trong localStorage vì backend hiện chưa có endpoint đổi tên.
