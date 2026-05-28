# Self-Healing AI CI/CD Failure Resolution System

An intelligent system that automatically detects, diagnoses, and resolves CI/CD pipeline failures using AI-powered analysis and remediation.

## Architecture Overview

```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐
│  Streamlit  │    │  FastAPI     │    │  DeepSeek    │
│  Frontend   │◄──►│  Backend     │◄──►│  AI Engine   │
└─────────────┘    └──────┬───────┘    └──────────────┘
                          │
                    ┌─────┴──────┐
                    │  SQLite    │
                    │  Database  │
                    └────────────┘
```

## Tech Stack

- **Backend**: Python, FastAPI, LangChain
- **Frontend**: Streamlit
- **AI**: DeepSeek API, HuggingFace Embeddings, FAISS
- **Database**: SQLite with SQLAlchemy
- **Infrastructure**: Docker

## Project Structure

```
self-healing-ci-agent/
├── app/                  # Backend application
│   ├── agents/           # AI agents (Phase 2+)
│   ├── api/              # API routes
│   ├── config/           # Settings & configuration
│   ├── dashboard/        # Dashboard logic
│   ├── database/         # DB setup & models
│   ├── github/           # GitHub API client
│   ├── parsers/          # Log parsers (Phase 2+)
│   ├── prompts/          # Prompt templates (Phase 2+)
│   ├── rag/              # RAG system (Phase 2+)
│   ├── utils/            # Shared utilities
│   ├── validation/       # Validation logic (Phase 2+)
│   ├── workflows/        # Workflow orchestration (Phase 2+)
│   └── main.py           # FastAPI entry point
├── frontend/             # Streamlit app
├── tests/                # Test suite
├── data/                 # Runtime data
├── docker/               # Docker resources
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd self-healing-ci-agent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and settings
   ```

5. **Run the backend**
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Run the frontend** (in a separate terminal)
   ```bash
   streamlit run frontend/streamlit_app.py
   ```

7. **Access the application**
   - FastAPI: http://localhost:8000
   - Streamlit: http://localhost:8501
   - API Docs: http://localhost:8000/docs

## Docker Setup

```bash
docker build -t self-healing-ci-agent .
docker run -p 8000:8000 --env-file .env self-healing-ci-agent
```

## Phase 1 - Current Status

- [x] Project structure
- [x] Configuration system
- [x] Logging setup
- [x] FastAPI backend
- [x] Streamlit frontend
- [x] Database setup
- [x] GitHub API client
- [x] DeepSeek API client
- [x] Utility functions
- [x] Docker support
