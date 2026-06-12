# Enterprise Agentic RAG System

> 🤖 Hệ thống Hỏi đáp nội bộ đa tài liệu với Local LLM, Agentic Routing, và Fine-tuning.

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.ai/) installed and running
- Docker & Docker Compose (for deployment)

### Installation

```bash
# Clone the repository
git clone https://github.com/QuyeN1104/RAGChatbot.git
cd RAGChatbot

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -e ".[dev]"

# Setup environment
cp .env.example .env
# Edit .env with your configuration
```

### Pull LLM Model

```bash
ollama pull llama3
```

### Run CLI

```bash
python main_cli.py
```

## 📁 Project Structure

```
├── src/
│   ├── core/          # Layer 1: Config, LLM Client, Logging
│   ├── rag/           # Layer 2: Document, Embedding, Retriever
│   ├── agent/         # Layer 3: Router, Memory, Tools
│   └── api/           # Layer 4: FastAPI Backend
├── ui/                # Streamlit Frontend
├── scripts/           # Fine-tuning & Evaluation
├── tests/             # Unit & Integration Tests
├── main_cli.py        # CLI Entry Point
└── pyproject.toml     # Project Configuration
```

## 🧪 Testing

```bash
pytest
```

## 📋 Project Timeline

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for the detailed 3-sprint roadmap.

## 📄 License

MIT
