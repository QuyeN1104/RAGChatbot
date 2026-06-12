# Enterprise Agentic RAG System — Project Plan

> **Phiên bản:** 2.0 · **Cập nhật:** 2026-06-13
> **Phương pháp:** Agile Scrum · **Sprint length:** 1 tuần · **Tổng:** 3 sprints

---

## 1. Tầm nhìn Dự án

Xây dựng hệ thống Hỏi đáp nội bộ đa tài liệu (RAG) cấp production với:
- **Local LLM** (Ollama) + fallback cloud API (Groq/OpenAI)
- **Agentic Routing** qua LangGraph state machine
- **Fine-tuning** mô hình với LoRA/Unsloth
- **Triển khai** Docker + CI/CD

---

## 2. Tech Stack

| Layer | Công nghệ | Vai trò |
|-------|-----------|---------|
| LLM Runtime | Ollama (Llama-3/Qwen) | Inference cục bộ |
| LLM Fallback | Groq / OpenAI API | Cloud fallback |
| Framework | LangChain + LangGraph | Orchestration & Agent |
| Vector DB | ChromaDB → Qdrant (mở rộng) | Lưu trữ & tìm kiếm vector |
| Embedding | `BAAI/bge-m3` | Nhúng đa ngôn ngữ |
| Re-ranker | `BAAI/bge-reranker-v2-m3` | Chấm điểm lại kết quả |
| Fine-tuning | Unsloth (LoRA/PEFT) | Tinh chỉnh mô hình |
| Backend | FastAPI | REST API |
| Frontend | Streamlit | Giao diện người dùng |
| Infra | Docker, Docker Compose | Containerization |
| CI/CD | GitHub Actions | Tự động hóa |

---

## 3. Kiến trúc Phân tầng (Layered Architecture)

```
┌─────────────────────────────────────────────────┐
│  Layer 4: Interfaces                            │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐ │
│  │ Streamlit│  │ FastAPI  │  │ CLI (main.py) │ │
│  └────┬─────┘  └────┬─────┘  └──────┬────────┘ │
├───────┼──────────────┼───────────────┼──────────┤
│  Layer 3: Agent & Orchestration                 │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐ │
│  │ Router   │  │ Memory   │  │ Tools         │ │
│  │(LangGraph│  │(History) │  │(RAG, Web, ...)│ │
│  └────┬─────┘  └────┬─────┘  └──────┬────────┘ │
├───────┼──────────────┼───────────────┼──────────┤
│  Layer 2: RAG Pipeline                          │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐ │
│  │ Document │  │ Embedding│  │ Retriever     │ │
│  │ Loader   │  │ Service  │  │ + Re-ranker   │ │
│  └────┬─────┘  └────┬─────┘  └──────┬────────┘ │
├───────┼──────────────┼───────────────┼──────────┤
│  Layer 1: Core Infrastructure                   │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐ │
│  │ Config   │  │ LLM      │  │ Exceptions    │ │
│  │ (.env)   │  │ Client   │  │ & Logger      │ │
│  └──────────┘  └──────────┘  └───────────────┘ │
└─────────────────────────────────────────────────┘
```

**Nguyên tắc thiết kế:**
1. **Dependency chỉ đi xuống** — Layer trên chỉ import layer dưới
2. **Interface Abstraction** — Mỗi service expose qua abstract class/protocol
3. **Lazy Initialization** — Tài nguyên nặng (LLM, Vector DB) chỉ khởi tạo khi cần
4. **Config-driven** — Mọi tham số qua `.env` + Pydantic Settings

---

## 4. Cấu trúc Thư mục

```text
agentic-rag-project/
├── .env.example                # Template biến môi trường
├── .github/
│   └── workflows/
│       └── ci.yml              # CI/CD pipeline
├── data/
│   ├── raw_pdfs/               # Tài liệu gốc
│   ├── vector_db/              # ChromaDB persistence
│   └── dataset/                # Fine-tuning data (.jsonl)
│
├── src/
│   ├── __init__.py
│   ├── core/                   # Layer 1: Foundation
│   │   ├── __init__.py
│   │   ├── config.py           # Pydantic Settings singleton
│   │   ├── llm_client.py       # LLM provider factory
│   │   ├── exceptions.py       # Custom exception hierarchy
│   │   └── logger.py           # Structured logging
│   │
│   ├── rag/                    # Layer 2: RAG Pipeline
│   │   ├── __init__.py
│   │   ├── document.py         # PDF loading + chunking
│   │   ├── embedding.py        # Embedding service
│   │   ├── retriever.py        # Semantic search + re-ranking
│   │   └── vector_store.py     # Vector DB abstraction
│   │
│   ├── agent/                  # Layer 3: Agent
│   │   ├── __init__.py
│   │   ├── state.py            # Agent state TypedDict
│   │   ├── router.py           # LangGraph state machine
│   │   ├── memory.py           # Conversation history
│   │   └── tools.py            # Agent tools registry
│   │
│   └── api/                    # Layer 4: Backend API
│       ├── __init__.py
│       ├── main.py             # FastAPI app factory
│       ├── routes.py           # Endpoint definitions
│       ├── schemas.py          # Pydantic request/response
│       └── dependencies.py     # Dependency injection
│
├── ui/
│   └── app.py                  # Streamlit frontend
│
├── scripts/
│   ├── generate_qa.py          # Sinh data fine-tuning
│   ├── finetune.py             # Huấn luyện LoRA
│   └── evaluate.py             # Đánh giá RAGAS
│
├── tests/
│   ├── conftest.py             # Shared fixtures
│   ├── test_core/
│   ├── test_rag/
│   └── test_agent/
│
├── main_cli.py                 # CLI entry point
├── Dockerfile.api
├── Dockerfile.ui
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## 5. Data Flow

### 5.1 Ingestion Flow (Upload → Vector DB)

```
User Upload PDF
      │
      ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│ document.py  │───▶│ embedding.py │───▶│vector_store │
│ load + chunk │    │ encode chunks│    │  upsert()   │
└─────────────┘    └──────────────┘    └─────────────┘
```

### 5.2 Query Flow (Question → Answer)

```
User Question
      │
      ▼
┌──────────┐   classify    ┌──────────────┐
│ router.py│──────────────▶│ INTERNAL_DOC │──┐
│ (intent) │               ├──────────────┤  │
│          │──────────────▶│ GENERAL_CHAT │  │
└──────────┘               └──────┬───────┘  │
                                  │          │
                    ┌─────────────┘          │
                    ▼                        ▼
            ┌──────────────┐      ┌──────────────────┐
            │ LLM direct   │      │ retriever.py     │
            │ (general)    │      │ search + rerank  │
            └──────┬───────┘      └────────┬─────────┘
                   │                       │
                   │              ┌────────▼─────────┐
                   │              │ LLM + context    │
                   │              │ (RAG answer)     │
                   │              └────────┬─────────┘
                   └───────┬───────────────┘
                           ▼
                   ┌───────────────┐
                   │  memory.py    │
                   │  save history │
                   └───────────────┘
```

---

## 6. Kế hoạch Sprint

### Sprint 1: Core RAG Pipeline (Ngày 1–7)

> **Mục tiêu:** Hệ thống RAG hoạt động end-to-end trên CLI

| Ngày | Task | File | Deliverable |
|------|------|------|-------------|
| 1 | Setup project + Layer 1 Foundation | `config.py`, `llm_client.py`, `exceptions.py`, `logger.py` | `.env` config load được, kết nối Ollama thành công |
| 2 | PDF Ingestion | `document.py` | Load PDF → chunks với metadata (source, page) |
| 3 | Embedding + Vector Store | `embedding.py`, `vector_store.py` | Chunks → vectors → ChromaDB, test similarity search |
| 4 | Retriever + RAG Chain | `retriever.py` | Semantic search → prompt assembly → LLM answer |
| 5 | Agent Router + Memory | `state.py`, `router.py`, `memory.py` | Intent classification, conversation context |
| 6 | CLI Integration | `main_cli.py` | Interactive chat loop trên terminal |
| 7 | **Sprint Review** | `tests/` | Unit tests pass, demo CLI chat với tài liệu thật |

**Definition of Done:**
- [ ] Upload PDF → hỏi câu hỏi về nội dung → nhận câu trả lời chính xác
- [ ] Conversation memory hoạt động (hỏi "cái đó là gì?" → hiểu context)
- [ ] Unit tests cho document.py, retriever.py (≥80% coverage)

#### Chi tiết hàm cần triển khai

**`src/core/config.py`** — Pydantic Settings
```python
class Settings(BaseSettings):
    # LLM
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    # Embedding
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    # Vector DB
    CHROMA_PERSIST_DIR: str = "./data/vector_db"
    CHROMA_COLLECTION: str = "documents"
    # RAG
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    TOP_K: int = 5

    model_config = SettingsConfigDict(env_file=".env")

def get_settings() -> Settings:  # Singleton via lru_cache
```

**`src/core/llm_client.py`** — LLM Provider Factory
```python
class LLMProvider(Protocol):
    def invoke(self, prompt: str) -> str: ...
    def stream(self, prompt: str) -> Iterator[str]: ...

def create_llm_client(provider: str = "ollama") -> LLMProvider:
    """Factory: 'ollama' | 'groq' | 'openai'"""
```

**`src/rag/document.py`** — Document Processing
```python
def load_pdf(file_path: str | Path) -> list[Document]:
    """PyPDFLoader → list of LangChain Documents with page metadata."""

def chunk_documents(docs: list[Document], chunk_size: int, overlap: int) -> list[Document]:
    """RecursiveCharacterTextSplitter, giữ nguyên metadata."""
```

**`src/rag/embedding.py`** — Embedding Service
```python
class EmbeddingService:
    def __init__(self, model_name: str): ...
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...
```

**`src/rag/vector_store.py`** — Vector DB Abstraction
```python
class VectorStoreManager:
    def __init__(self, settings: Settings): ...
    def add_documents(self, docs: list[Document]) -> list[str]: ...
    def similarity_search(self, query: str, k: int) -> list[Document]: ...
    def delete_collection(self) -> None: ...
```

**`src/rag/retriever.py`** — Retrieval + Generation
```python
def retrieve_context(query: str, store: VectorStoreManager, top_k: int) -> list[Document]:
    """Semantic search, trả về top_k documents."""

def generate_answer(query: str, context: list[Document], llm: LLMProvider) -> str:
    """Ghép context vào prompt template → gọi LLM."""
```

**`src/agent/router.py`** — Intent Router
```python
def classify_intent(query: str, llm: LLMProvider) -> Literal["INTERNAL_DOC", "GENERAL_CHAT"]:
    """Dùng LLM nhỏ hoặc regex heuristic để phân loại."""

def execute_route(intent: str, query: str, rag_chain, llm: LLMProvider) -> str:
    """Dispatch tới RAG hoặc direct LLM."""
```

**`src/agent/memory.py`** — Conversation Memory
```python
class ConversationMemory:
    def add(self, user_msg: str, ai_msg: str, session_id: str) -> None: ...
    def get_history(self, session_id: str, last_n: int = 5) -> list[dict]: ...
    def reformulate_query(self, query: str, history: list[dict], llm: LLMProvider) -> str: ...
```

---

### Sprint 2: Fine-tuning & Backend API (Ngày 8–14)

> **Mục tiêu:** Fine-tune mô hình, nâng cấp retrieval, expose REST API

| Ngày | Task | File | Deliverable |
|------|------|------|-------------|
| 8 | Sinh dữ liệu QA tự động | `scripts/generate_qa.py` | File `.jsonl` với ≥200 cặp QA |
| 9–10 | Fine-tuning LoRA + Export | `scripts/finetune.py` | Model GGUF chạy được trên Ollama |
| 11 | Re-ranking upgrade | `retriever.py` (update) | Cross-encoder re-rank, đo improvement |
| 12 | FastAPI Backend | `api/main.py`, `routes.py`, `schemas.py` | `/chat` + `/upload` endpoints hoạt động |
| 13 | Dependency Injection + Error handling | `api/dependencies.py` | Centralized DI, proper HTTP errors |
| 14 | **Sprint Review** | Dockerfile.api | API chạy trong Docker, Postman test pass |

**Definition of Done:**
- [ ] Fine-tuned model trả lời tốt hơn base model (đo bằng RAGAS)
- [ ] API `/chat` trả về JSON response đúng schema
- [ ] API `/upload` nhận PDF, tự động ingest vào Vector DB
- [ ] Dockerfile.api build & run thành công

#### Chi tiết hàm cần triển khai

**`scripts/generate_qa.py`** — Data Generation
```python
def generate_qa_from_chunk(chunk: str, llm: LLMProvider) -> list[dict]:
    """Prompt LLM sinh 2-3 cặp QA từ mỗi chunk.
    Return: [{"instruction": ..., "input": ..., "output": ...}]
    """

def build_dataset(pdf_dir: str, output_path: str) -> int:
    """Pipeline: load PDFs → chunk → generate QA → save JSONL."""
```

**`scripts/finetune.py`** — LoRA Training
```python
def load_base_model(model_name: str) -> tuple[Model, Tokenizer]:
    """Unsloth FastLanguageModel.from_pretrained()"""

def format_training_prompt(example: dict) -> str:
    """Alpaca/ChatML template formatting."""

def train(model, tokenizer, dataset_path: str, output_dir: str) -> None:
    """SFTTrainer với LoRA config (r=16, alpha=32)."""

def export_gguf(model_dir: str, quant: str = "q4_k_m") -> str:
    """Lượng tử hóa → file .gguf → nạp Ollama."""
```

**`src/rag/retriever.py`** — Thêm Re-ranking
```python
class ReRanker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"): ...
    def rerank(self, query: str, documents: list[Document], top_n: int) -> list[Document]:
        """Cross-encoder scoring → sort → top_n."""

def retrieve_and_rerank(query, store, reranker, top_k, top_n) -> list[Document]:
    """Two-stage: retrieve top_k → rerank → top_n."""
```

**`src/api/schemas.py`** — API Models
```python
class ChatRequest(BaseModel):
    message: str
    session_id: str = Field(default_factory=lambda: str(uuid4()))

class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceRef]
    session_id: str

class SourceRef(BaseModel):
    document: str
    page: int
    relevance: float
```

**`src/api/routes.py`** — Endpoints
```python
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, deps = Depends(get_deps)): ...

@router.post("/upload")
async def upload_document(file: UploadFile, deps = Depends(get_deps)): ...

@router.get("/health")
async def health_check(): ...
```

---

### Sprint 3: Frontend, DevOps & Production (Ngày 15–21)

> **Mục tiêu:** UI hoàn chỉnh, Docker Compose, CI/CD, deploy

| Ngày | Task | File | Deliverable |
|------|------|------|-------------|
| 15 | Streamlit UI | `ui/app.py` | Chat interface + file upload sidebar |
| 16 | Docker Compose | `docker-compose.yml`, `Dockerfile.ui` | `docker compose up` chạy toàn bộ |
| 17 | CI/CD Pipeline | `.github/workflows/ci.yml` | Auto lint + test + build on push |
| 18 | RAGAS Evaluation | `scripts/evaluate.py` | Báo cáo điểm Faithfulness, Context Precision |
| 19 | Monitoring + Logging | Cấu hình tập trung | Structured logs, health checks |
| 20–21 | **Final Review** | `README.md` | Docs hoàn chỉnh, demo end-to-end |

**Definition of Done:**
- [ ] `docker compose up` → 3 services (api, ui, vectordb) chạy ổn định
- [ ] UI: upload PDF, chat, xem sources — mượt mà
- [ ] CI pipeline: push code → auto test → build Docker image
- [ ] README có hướng dẫn cài đặt, sơ đồ kiến trúc, demo GIF
- [ ] RAGAS evaluation report với ≥ 3 metrics

#### Chi tiết hàm cần triển khai

**`ui/app.py`** — Streamlit Frontend
```python
def render_sidebar():
    """Upload PDF, hiển thị danh sách tài liệu đã upload."""

def render_chat():
    """Chat interface với st.chat_message, streaming response."""

def call_api(message: str, session_id: str) -> ChatResponse:
    """requests.post() tới FastAPI backend."""
```

**`docker-compose.yml`** — Service Orchestration
```yaml
services:
  api:
    build: { dockerfile: Dockerfile.api }
    ports: ["8000:8000"]
    volumes: ["./data:/app/data"]
    environment: { OLLAMA_BASE_URL: "http://host.docker.internal:11434" }

  ui:
    build: { dockerfile: Dockerfile.ui }
    ports: ["8501:8501"]
    depends_on: [api]

  # Mở rộng: thêm qdrant service khi scale
```

**`scripts/evaluate.py`** — RAGAS Evaluation
```python
def build_eval_dataset(qa_path: str, rag_chain) -> EvaluationDataset:
    """Load QA pairs → generate RAG answers → build dataset."""

def run_evaluation(dataset: EvaluationDataset) -> dict[str, float]:
    """RAGAS metrics: faithfulness, answer_relevancy, context_precision."""

def generate_report(results: dict, output_path: str) -> None:
    """Xuất báo cáo markdown với bảng điểm."""
```

---

## 7. Hướng mở rộng sau Sprint 3

| Tính năng | Mô tả | Ưu tiên |
|-----------|--------|---------|
| **Multi-user Auth** | JWT + session management | P1 |
| **Qdrant Migration** | Chuyển từ ChromaDB → Qdrant cho scale | P1 |
| **LangGraph Agent** | Nâng router thành state machine với tool calling | P1 |
| **Streaming Response** | SSE streaming từ API → UI | P2 |
| **Multi-format Ingest** | Hỗ trợ DOCX, TXT, Markdown | P2 |
| **Hybrid Search** | BM25 + Dense retrieval | P2 |
| **Admin Dashboard** | Quản lý documents, xem metrics | P3 |
| **Multi-tenant** | Namespace isolation per team | P3 |

---

## 8. Risk Matrix

| Risk | Impact | Mitigation |
|------|--------|------------|
| Ollama quá chậm trên CPU | Cao | Fallback sang Groq API (free tier) |
| Fine-tune thiếu GPU | Cao | Dùng Google Colab T4 (free) |
| ChromaDB không scale | Trung bình | Thiết kế VectorStoreManager abstract → swap sang Qdrant |
| PDF phức tạp (bảng, hình) | Trung bình | Bắt đầu với text-only, mở rộng multimodal sau |