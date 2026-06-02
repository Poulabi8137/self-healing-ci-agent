# Contributing

Thank you for your interest in the Self-Healing CI/CD Agent. This document provides guidelines for contributing to the project.

## Table of Contents

- [Setup Instructions](#setup-instructions)
- [Development Workflow](#development-workflow)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)

---

## Setup Instructions

### Prerequisites

- Python 3.12 or later
- Node.js 20 or later
- Git
- [DeepSeek API key](https://platform.deepseek.com) (for LLM features)
- GitHub token with `repo` scope (for PR automation)

### Local Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/self-healing-ci-agent.git
cd self-healing-ci-agent

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate      # Linux/macOS
# venv\Scripts\activate       # Windows

# Install all dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — set DEEPSEEK_API_KEY and GITHUB_TOKEN
```

### Running the Application

```bash
# Backend (terminal 1)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend dashboard (terminal 2)
cd frontend
npm install
npm run dev
```

The API is available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_auth.py -v

# Run with coverage (install coverage.py first)
coverage run -m pytest tests/
coverage report
```

---

## Development Workflow

### Branching Strategy

- `main` — stable, release-ready code
- `feature/<name>` — new features (branched from `main`)
- `fix/<name>` — bug fixes (branched from `main`)

### Development Cycle

1. **Pick an issue** — Check open issues or create a new one describing the feature or bug.
2. **Create a branch** — `git checkout -b feature/my-feature`
3. **Write code** — Follow the coding standards below.
4. **Write tests** — All new code must include tests. Maintain or improve existing test patterns.
5. **Run tests locally** — `pytest tests/ -v` — all tests must pass.
6. **Commit** — Use clear, conventional commit messages.
7. **Push and open a PR** — See [Pull Request Process](#pull-request-process).

### Commit Message Convention

Follow conventional commits:

```
<type>: <short description>

<optional body>
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `chore`, `ci`

Examples:
- `feat: add exponential backoff to retry utility`
- `fix: prevent rate limiter key collision on auth endpoints`
- `docs: update API reference with circuit breaker section`

---

## Pull Request Process

1. **Ensure tests pass** — Run `pytest tests/ -v` and confirm all tests pass.
2. **Update documentation** — If your change affects the API, workflow, or configuration, update the relevant docs in `docs/`.
3. **Update the CHANGELOG** — Add an entry under the `[Unreleased]` section describing your change.
4. **Open the PR** — Against the `main` branch. Provide a clear description of what the change does and why.
5. **CI checks** — All GitHub Actions checks must pass (lint, test).
6. **Review** — At least one reviewer should approve the PR before merging.
7. **Merge** — Squash-merge into `main` with a clean commit message.

### PR Checklist

- [ ] Tests added/updated and passing
- [ ] Documentation updated (if applicable)
- [ ] CHANGELOG updated
- [ ] `.env.example` updated (if new environment variables added)
- [ ] No new warnings introduced
- [ ] Code follows existing conventions and style

---

## Coding Standards

### Python Style

- **Python 3.12+** — Use modern Python features (type hints, pattern matching, etc.)
- **PEP 8** — Follow standard Python style. 4 spaces for indentation.
- **Type hints** — All function signatures must have type annotations.
- **Docstrings** — Use triple-quote docstrings for public modules, classes, and functions.

### Project Conventions

| Area | Convention |
|------|-----------|
| **Imports** | Standard library → third-party → project modules (alphabetical within groups) |
| **Naming** | `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_CASE` for constants |
| **Async** | Use `async def` for I/O-bound operations. Wrap sync DB/API calls with `asyncio.to_thread()` |
| **Error handling** | Use `try/except` with specific exception types. Sanitize error messages before returning to clients. Log the original error server-side. |
| **Logging** | Use `get_logger(__name__)` at module level. Bind context with `.bind(request_id=...)`. |
| **Pydantic models** | Use `Field(..., max_length=N)` for all string fields. Use `Field(default=...)` for optional fields. |
| **Dependencies** | FastAPI dependencies via `Depends()`. Prefer `require_authenticated`, `require_recruiter`, `require_admin` over manual auth checks. |

### Testing Standards

- **pytest** — All tests use pytest. No unittest.TestCase.
- **Async tests** — Use `@pytest.mark.asyncio` for async test functions.
- **Test isolation** — Each test should be independent. Use `autouse` fixtures for setup/teardown.
- **No external calls** — Tests should not make real API calls to DeepSeek or GitHub.
- **Minimum coverage** — New code should maintain or improve line coverage.

### Project Structure

```
app/                    # Backend application
  agents/               # AI agent implementations
  api/                  # FastAPI route handlers
  config/               # Pydantic settings
  dashboard/            # Metrics and analytics
  database/             # SQLAlchemy models and DB setup
  github/               # GitHub API integration
  parsers/              # Log and error parsing
  prompts/              # LLM prompt templates
  rag/                  # RAG indexing and retrieval
  utils/                # Shared utilities (logging, retry, circuit breaker)
  validation/           # Validation engine
  workflows/            # Workflow orchestrators
frontend/               # React 19 + TypeScript + Vite SPA
  src/
    components/         # Reusable UI components
    pages/              # Route pages (11 pages)
    lib/                # Auth, API client, demo data
    test/               # 59 frontend tests
tests/                  # 259 backend tests
docs/                   # Documentation
docker/                 # Docker Compose files
```

---

## Questions?

Open a GitHub Discussion or issue. We welcome questions, suggestions, and feedback.
