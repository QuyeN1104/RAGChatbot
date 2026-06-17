<div align="center">
  <img src="docs/assets/banner.png" alt="Enterprise Agentic RAG System Banner" width="100%">

  # 🚀 Enterprise Agentic RAG System

  **Hệ thống Hỏi đáp nội bộ đa tài liệu với Local LLM, Agentic Routing, và Fine-tuning.**

  <p align="center">
    <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python" alt="Python" />
    <img src="https://img.shields.io/badge/LangChain-Enabled-green?style=for-the-badge&logo=chainlink" alt="LangChain" />
    <img src="https://img.shields.io/badge/Ollama-Local%20LLM-orange?style=for-the-badge" alt="Ollama" />
    <img src="https://img.shields.io/badge/pytest-passing-brightgreen?style=for-the-badge&logo=pytest" alt="Pytest" />
  </p>

</div>

---

## 🌟 Giới thiệu (Overview)

**Enterprise Agentic RAG System** là một hệ thống trò chuyện AI thông minh được xây dựng để hỗ trợ doanh nghiệp truy xuất và hỏi đáp nội dung trên các tài liệu nội bộ. Hệ thống sử dụng kiến trúc **RAG (Retrieval-Augmented Generation)** kết hợp với **Agentic Routing** giúp AI có khả năng tự động phân loại câu hỏi (hỏi văn bản hay giao tiếp thông thường) và duy trì ngữ cảnh trò chuyện cực kỳ hiệu quả.

<div align="center">
  <img src="docs/assets/cli_demo.png" alt="CLI Demo Interface" width="80%">
  <br/>
  <i>Minh hoạ giao diện sử dụng CLI siêu mượt mà của hệ thống.</i>
</div>

---

## 🚀 Hướng dẫn Cài đặt & Khởi chạy (How to Run)

### 1️⃣ Yêu cầu hệ thống (Prerequisites)
- **Python:** Phiên bản 3.10 trở lên.
- **Ollama:** Đã cài đặt và đang chạy ở chế độ nền (để cung cấp Local LLM).
- **Hệ điều hành:** Hỗ trợ tốt nhất trên Linux/macOS.

### 2️⃣ Cài đặt (Installation)
Tiến hành tải mã nguồn và cài đặt các thư viện cần thiết:

```bash
# 1. Clone repository
git clone https://github.com/QuyeN1104/RAGChatbot.git
cd RAGChatbot

# 2. Tạo môi trường ảo (Khuyên dùng uv hoặc venv)
python -m venv .venv
source .venv/bin/activate  # Trên Windows dùng: .venv\Scripts\activate

# 3. Cài đặt các package và dependencies
pip install -e ".[dev]"

# 4. Cấu hình biến môi trường
cp .env.example .env
# (Bạn có thể mở file .env để tinh chỉnh các thông số nếu cần)
```

### 3️⃣ Chuẩn bị Model (Pull LLM Model)
Hệ thống sử dụng model `llama3` mặc định thông qua Ollama.

```bash
ollama pull llama3
```

### 4️⃣ Khởi chạy ứng dụng (Run the App)
Khởi động giao diện CLI bằng câu lệnh:

```bash
python main_cli.py
```

Sau khi chạy, giao diện dòng lệnh sẽ xuất hiện, tự động tải các tài liệu PDF trong thư mục `data/` và sẵn sàng trả lời các câu hỏi của bạn. Hệ thống cũng có khả năng **lưu lại phiên làm việc (Session)** để bạn có thể tắt và mở lại mà không mất lịch sử trò chuyện!

---

## 🧪 Hướng dẫn Chạy Test (Run Tests)

Dự án được đảm bảo chất lượng với độ phủ mã (Coverage) trên 80%. Bạn có thể tự mình kiểm chứng bộ Unit Test toàn diện bằng câu lệnh dưới đây:

### Chạy toàn bộ Test và hiển thị Coverage
```bash
# Nếu bạn dùng `uv`
uv run pytest tests/test_rag/ tests/test_agent/ --cov=src.rag --cov=src.agent --cov-report=term-missing

# Nếu bạn dùng `pip` thông thường
pytest tests/test_rag/ tests/test_agent/ --cov=src.rag --cov=src.agent --cov-report=term-missing
```

### Chạy test rút gọn
```bash
pytest -v
```

---

## 📁 Cấu trúc Dự án (Project Structure)

```text
├── src/
│   ├── core/          # Layer 1: Config, LLM Client, Logging
│   ├── rag/           # Layer 2: Document processing, Embedding, Retriever
│   ├── agent/         # Layer 3: Router (Phân loại intent), Memory, Tools
│   └── api/           # Layer 4: FastAPI Backend (Sắp ra mắt)
├── docs/
│   └── assets/        # Hình ảnh, banner, demo video cho dự án
├── scripts/           # Fine-tuning & Evaluation pipelines
├── tests/             # Unit & Integration Tests (Sử dụng Pytest & Mocks)
├── main_cli.py        # File thực thi CLI chính
└── pyproject.toml     # File cấu hình thư viện dự án
```

---

## 📋 Lộ trình phát triển (Roadmap)
Để xem chi tiết kế hoạch 3 Sprints phát triển dự án này, vui lòng tham khảo file [PROJECT_PLAN.md](PROJECT_PLAN.md).

## 📄 Bản quyền (License)
Dự án được phân phối dưới giấy phép [MIT](LICENSE).
