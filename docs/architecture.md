# Architecture

## 1. System Overview

The Self-Healing CI/CD Agent is built on a modular architecture using FastAPI as the core backend framework and React 19 for the frontend. The system is organized into distinct layers that handle specific responsibilities, from data ingestion to workflow orchestration to presentation.

### High-Level Block Diagram

```mermaid
graph TB
    subgraph Input
        LOGS[CI/CD Logs]
        REPO[Repository Code]
    end

    subgraph "Self-Healing CI Agent"
        API[FastAPI Server<br/>20 Endpoints]
        RAG[RAG Engine<br/>FAISS + Sentence Transformers]
        AG[AI Agent Pool<br/>8 Agents]
        VAL[Validation Engine<br/>AST → Build → Test]
        WKF[Workflow Orchestrator<br/>6 Workflows]
        DB[(Database)]
    end

    subgraph Output
        DASH[React Dashboard<br/>11 Pages]
        PR[GitHub Pull Request]
    end

    LOGS --> API
    REPO --> RAG
    API --> WKF
    WKF --> AG
    RAG --> AG
    WKF --> VAL
    VAL --> WKF
    WKF --> DB
    DB --> DASH
    WKF --> PR
    AG -->|DeepSeek/Groq| LLM[(LLM API)]
```

---

## 2. Layer Architecture

### 2.1 API Layer (`app/api/`)

Entry points for all external interactions. Uses FastAPI routers with clear separation:

- **System Routes** — Health checks and versioning
- **RAG Routes** — Repository indexing and context retrieval
- **Analysis Routes** — CI/CD failure analysis
- **Fix Routes** — AI-powered fix generation
- **Validation Routes** — Multi-stage validation pipeline
- **Retry Routes** — Self-healing retry loop
- **Review Routes** — Multi-agent code review
- **PR Routes** — Pull request automation
- **Dashboard Routes** — Metrics, analytics, and benchmarks

All routes use Pydantic models for request validation and follow consistent error handling patterns.

### 2.2 Agent Layer (`app/agents/`)

8 specialized AI agents, each responsible for a specific task:

| Agent | Responsibility | Prompt Template |
|-------|---------------|-----------------|
| Debug Agent | Analyzes CI/CD logs to identify root cause | `debug_prompt.py` |
| Fix Agent | Generates code fixes using RAG context | `fix_prompt.py` |
| Retry Agent | Implements adaptive retry strategies | `retry_prompt.py` |
| Review Orchestrator | Coordinates multi-agent review | `review_prompt.py` |
| Security Reviewer | Scans for security vulnerabilities | `security_reviewer_prompt.py` |
| Performance Reviewer | Evaluates performance impact | `performance_reviewer_prompt.py` |
| Quality Reviewer | Assesses code quality | `quality_reviewer_prompt.py` |
| Coverage Reviewer | Checks test coverage adequacy | `coverage_reviewer_prompt.py` |

### 2.3 RAG Layer (`app/rag/`)

Retrieval-Augmented Generation pipeline for context-aware debugging:

- **Repository Loader** — Clones and loads repositories
- **Chunking** — Splits code into semantically meaningful chunks
- **Embedding** — Generates vector embeddings using Sentence Transformers
- **Vector Store** — FAISS-based vector index for similarity search
- **Retriever** — Queries the vector store for relevant context
- **Indexing Pipeline** — Orchestrates the full indexing workflow

### 2.4 Validation Layer (`app/validation/`)

Multi-stage validation pipeline:

- **Syntax Validator** — Validates Python syntax using `ast.parse`
- **Build Validator** — Checks project structure, config files, imports
- **Test Runner** — Executes pytest and captures failures
- **Validation Service** — Orchestrates the full validation pipeline

### 2.5 Workflow Layer (`app/workflows/`)

Orchestration layer that coordinates agents, RAG, validation, and persistence:

- **Analysis Workflow** — Coordinates debug analysis with RAG context
- **Fix Generation Workflow** — Generates and applies fixes
- **Validation Workflow** — Runs full validation pipeline
- **Retry Workflow** — Implements adaptive self-healing loop
- **Review Workflow** — Runs multi-agent review pipeline
- **PR Workflow** — Orchestrates PR creation

### 2.6 Frontend Layer (`frontend/src/`)

React 19 + TypeScript 6 SPA with 11 pages:

- **Public pages** — Landing, Login
- **Authenticated pages** — Dashboard, Analysis, Validation, Retry, Review, PR, Indexing, Tasks, Admin Keys
- **Shared components** — Layout, SpotlightCard, TiltCard, AnimatedCounter, MetricCard, Skeleton, StatusBadge
- **Data layer** — React Query (30s stale time), AuthProvider (sessionStorage)
- **Animation** — Framer Motion with AnimatePresence page transitions

---

## 3. Component Tree (React)

```mermaid
graph TB
    subgraph "React SPA"
        App --> AuthProvider
        App --> QueryClientProvider
        App --> BrowserRouter
        App --> Toaster

        BrowserRouter --> PublicGuard
        BrowserRouter --> AuthGuard

        PublicGuard --> Landing
        PublicGuard --> Login

        AuthGuard --> Layout
        Layout --> Sidebar
        Layout --> TabNav
        Layout --> ErrorBoundary

        ErrorBoundary --> AnimatePresence

        subgraph "Lazy Loaded Pages"
            AnimatePresence --> Dashboard
            AnimatePresence --> Analysis
            AnimatePresence --> Validation
            AnimatePresence --> Retry
            AnimatePresence --> Review
            AnimatePresence --> PR
            AnimatePresence --> Indexing
            AnimatePresence --> Tasks
            AnimatePresence --> AdminKeys
        end

        CommandPalette --> App
    end

    subgraph "Shared Components"
        SpotlightCard
        TiltCard
        AnimatedCounter
        MetricCard
        Skeleton
        StatusBadge
    end

    Dashboard --> MetricCard
    Dashboard --> SpotlightCard
    Dashboard --> TiltCard
    Dashboard --> AnimatedCounter
    Dashboard --> Skeleton

    Review --> SpotlightCard
    Review --> AnimatedCounter

    Retry --> SpotlightCard
    Retry --> AnimatedCounter
```

---

## 4. Frontend Architecture

```mermaid
graph LR
    subgraph "Routing (react-router-dom v7)"
        LA[lazy dashboard]
        LB[lazy analysis]
        LC[lazy validation]
        LD[lazy retry]
        LE[lazy review]
        LF[lazy pr]
        LG[lazy indexing]
        LH[lazy tasks]
        LI[lazy admin-keys]
    end

    subgraph "Data Layer"
        RQ[React Query<br/>staleTime: 30s]
        API[REST Client<br/>fetch()]
        Auth[AuthProvider<br/>sessionStorage]
    end

    subgraph "UI Layer"
        FM[Framer Motion<br/>spring animations]
        RC[Recharts<br/>8 chart types]
        TAIL[Tailwind CSS v4]
        LU[Lucide Icons]
    end

    subgraph "Pages (11)"
        LND[Landing]
        LGN[Login]
        DSH[Dashboard]
        ANL[Analysis]
        VAL[Validation]
        RTY[Retry]
        RVW[Review]
        PR[PR]
        IDX[Indexing]
        TSK[Tasks]
        ADM[Admin Keys]
    end

    LA --> DSH
    LB --> ANL
    LC --> VAL
    LD --> RTY
    LE --> RVW
    LF --> PR
    LG --> IDX
    LH --> TSK
    LI --> ADM

    DSH --> RQ
    ANL --> RQ
    VAL --> RQ
    RTY --> RQ
    RVW --> RQ
    PR --> RQ
    IDX --> RQ
    TSK --> RQ
    ADM --> Auth

    DSH --> RC
    RVW --> RC
    RTY --> RC

    DSH --> FM
    LND --> FM
    LVL --> FM
```

---

## 5. Backend Architecture

```mermaid
graph TB
    subgraph "FastAPI Server"
        API[API Layer<br/>9 Routers / 20 Endpoints]
        MID[Middleware<br/>Rate Limiter, CORS, Auth, Request ID]
    end

    subgraph "Workflow Layer"
        W1[Analysis Workflow]
        W2[Fix Generation Workflow]
        W3[Validation Workflow]
        W4[Retry Workflow]
        W5[Review Workflow]
        W6[PR Workflow]
    end

    subgraph "Agent Layer"
        A1[Debug Agent]
        A2[Fix Agent]
        A3[Retry Agent]
        A4[Review Orchestrator]
        A5[Security Reviewer]
        A6[Performance Reviewer]
        A7[Quality Reviewer]
        A8[Coverage Reviewer]
    end

    subgraph "RAG Layer"
        R1[Repository Loader]
        R2[Chunker]
        R3[Embedder<br/>Sentence Transformers]
        R4[FAISS Vector Store]
        R5[Retriever]
    end

    subgraph "Validation Layer"
        V1[Syntax Validator<br/>ast.parse]
        V2[Build Validator<br/>structure + config]
        V3[Test Runner<br/>pytest]
    end

    subgraph "Data Layer"
        DB[(SQLite<br/>SQLAlchemy)]
        CFG[Pydantic Settings<br/>.env]
    end

    subgraph "Integration"
        GH[GitHub API<br/>PyGithub]
        LLM[LLM Provider<br/>DeepSeek / Groq]
        LOG[Loguru<br/>structured logging]
        CB[Circuit Breaker]
    end

    API --> MID
    MID --> W1
    MID --> W2
    MID --> W3
    MID --> W4
    MID --> W5
    MID --> W6

    W1 --> A1
    W2 --> A2
    W3 --> V1
    W3 --> V2
    W3 --> V3
    W4 --> A3
    W5 --> A4
    A4 --> A5
    A4 --> A6
    A4 --> A7
    A4 --> A8
    W6 --> GH

    W1 --> R5
    W2 --> R5
    R5 --> R4
    R4 --> R3
    R3 --> R2
    R2 --> R1

    A1 --> LLM
    A2 --> LLM
    A3 --> LLM
    A5 --> LLM
    A6 --> LLM
    A7 --> LLM
    A8 --> LLM

    W1 --> DB
    W2 --> DB
    W3 --> DB
    W4 --> DB
    W5 --> DB
    W6 --> DB

    LLM --> CB
    GH --> CB
```

---

## 6. Request Flow

### End-to-End Sequence: Analysis → Fix → Validate → Retry → Review → PR

```mermaid
sequenceDiagram
    actor User
    participant UI as React SPA
    participant API as FastAPI Server
    participant WKF as Workflow Orchestrator
    participant LLM as AI Agent Pool
    participant RAG as RAG Pipeline
    participant VAL as Validation Engine
    participant GH as GitHub API
    participant DB as Database

    Note over User,DB: Analysis & Fix Flow
    User->>UI: Enter CI/CD logs
    UI->>API: POST /analysis/debug
    API->>WKF: Start Analysis Workflow
    WKF->>RAG: Retrieve relevant code context
    RAG-->>WKF: Code snippets + file paths
    WKF->>LLM: Debug Agent: classify & analyze
    LLM-->>WKF: {error_category, root_cause}
    WKF->>DB: Save analysis result
    WKF-->>API: AnalysisResult
    API-->>UI: Return analysis
    UI->>User: Display root cause + context

    Note over User,DB: Fix Generation Flow
    User->>UI: Generate fix
    UI->>API: POST /fix/generate
    API->>WKF: Start Fix Workflow
    WKF->>RAG: Retrieve additional context
    WKF->>LLM: Fix Agent: generate patch
    LLM-->>WKF: {patch, modified_files}
    WKF->>DB: Save fix result
    WKF-->>API: FixResult
    API-->>UI: Return fix (patch + summary)

    Note over User,DB: Validation Flow (automatic)
    WKF->>VAL: Validate fix (AST + build + test)
    VAL-->>WKF: {syntax, build, tests}

    alt Validation Failed
        Note over WKF,LLM: Retry Loop
        loop Up to MAX_RETRIES
            WKF->>LLM: Retry Agent: improve fix
            LLM-->>WKF: Revised patch
            WKF->>VAL: Re-validate
            VAL-->>WKF: ValidationResult
        end
    end

    Note over User,DB: Multi-Agent Review
    WKF->>LLM: Review Orchestrator: evaluate
    LLM-->>WKF: {security, perf, quality, coverage}

    alt Review Approved
        Note over User,DB: PR Creation
        WKF->>GH: Create branch → commit → PR
        GH-->>WKF: {pr_url, branch}
    else Dry Run
        WKF-->>WKF: Simulate only
    end

    WKF->>DB: Persist all results
    DB-->>WKF: confirmed
    WKF-->>API: WorkflowResult
    API-->>UI: {status, scores, pr_url}
    UI->>User: Display final result
```

---

## 7. Data Flow

```mermaid
flowchart LR
    subgraph Input
        LOGS[CI/CD Logs]
        REPO[Repository Code]
    end

    subgraph Processing
        RAG[RAG Pipeline]
        AG[AI Agents]
        VAL[Validation]
        WKF[Workflows]
    end

    subgraph Storage
        DB[(SQLite)]
        VS[(Vector Store<br/>FAISS)]
    end

    subgraph Output
        DASH[React Dashboard]
        API[API Response]
        PR[GitHub PR]
    end

    LOGS --> WKF
    REPO --> RAG
    RAG --> VS
    VS --> AG
    AG --> WKF
    WKF --> VAL
    VAL --> WKF
    WKF --> DB
    DB --> DASH
    WKF --> API
    WKF --> PR
```

---

## 8. Deployment Architecture

```mermaid
graph TB
    subgraph "Development"
        DEV_BACK[uvicorn<br/>localhost:8000]
        DEV_FRONT[vite dev<br/>localhost:5173]
    end

    subgraph "Production (Docker Compose)"
        subgraph "Docker Network"
            CADDY[Caddy<br/>Reverse Proxy<br/>:80 → :443]
            API_PROD[gunicorn + uvicorn<br/>:8000]
            STATIC[vite build<br/>static files]
        end
        DATA[(SQLite Volume)]
    end

    subgraph "External"
        LLM_API[DeepSeek API]
        GITHUB[GitHub API]
        USER_BROWSER[Browser]
    end

    USER_BROWSER --> CADDY
    CADDY --> API_PROD
    CADDY --> STATIC
    API_PROD --> LLM_API
    API_PROD --> GITHUB
    API_PROD --> DATA
```

---

## 9. Security Architecture

```mermaid
sequenceDiagram
    actor User
    participant UI as React SPA
    participant API as FastAPI
    participant Auth as Auth Middleware
    participant Rate as Rate Limiter
    participant CB as Circuit Breaker
    participant LLM as LLM API
    participant DB as Database

    User->>UI: Enter API key
    UI->>API: Request + Authorization header
    API->>Rate: Check rate limit
    Rate-->>API: allowed / blocked

    alt Rate Limited
        API-->>UI: 429 Too Many Requests
        UI->>User: Rate limit warning
    else Allowed
        API->>Auth: Verify API key (SHA-256 hash)
        Auth->>DB: Lookup hashed key
        DB-->>Auth: role + permissions
        Auth-->>API: user context (role)

        alt Invalid Key
            API-->>UI: 401 Unauthorized
        else Valid Key
            API->>CB: Forward to external API
            CB-->>LLM: Pass through

            alt Circuit Open
                API-->>UI: 503 Service Unavailable
            else Circuit Closed
                LLM-->>CB: Response
                CB-->>API: Forward response
                API-->>UI: Success response
                UI->>User: Display result
            end
        end
    end
```

---

## 10. Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Web Framework** | FastAPI 0.115 | Async Python API server |
| **Web Server** | gunicorn + uvicorn | Multi-worker production deployment |
| **AI Framework** | LangChain 1.0 | LLM abstraction and agent chaining |
| **LLM Providers** | DeepSeek API, Groq | AI reasoning, analysis, and code generation |
| **Vector Search** | FAISS + Sentence Transformers | Semantic code search for RAG context |
| **Database** | SQLite + SQLAlchemy | Data persistence |
| **Frontend** | React 19 + TypeScript 6 | 11-page SPA dashboard |
| **Build Tool** | Vite 8 | Fast dev server and optimized builds |
| **Styling** | Tailwind CSS v4 | Utility-first CSS framework |
| **Charts** | Recharts 3.8 | Interactive data visualizations |
| **Animation** | Framer Motion 12 | Spring animations, page transitions |
| **Icons** | Lucide React | Consistent icon set |
| **Data Fetching** | TanStack React Query 5 | Server state management and caching |
| **Auth** | sessionStorage + SHA-256 | Secure token storage |
| **Logging** | Loguru | Structured rotating logs |
| **Container** | Docker + Docker Compose + Caddy | Deployment packaging and reverse proxy |
| **CI/CD** | GitHub Actions | Automated linting, testing, and building |

---

## 11. Design Decisions

1. **SQLite for development** — Zero-config database suitable for single-node deployments; PostgreSQL adapter available for production.

2. **FAISS for vector search** — Lightweight, in-process vector store that avoids external service dependencies.

3. **Code-split routing** — 9 lazy-loaded routes reduce main bundle to 440 KB; each page chunk loads only when navigated to.

4. **React Query for data fetching** — Automatic caching, deduplication, stale-while-revalidate; 30s staleTime reduces API calls.

5. **Framer Motion for animations** — Spring physics for natural-feeling UI motion; AnimatePresence for smooth page transitions.

6. **SessionStorage for auth** — Tokens survive page refresh but not tab close; harder to exfiltrate than localStorage.

7. **Workflow-based orchestration** — Each pipeline phase is a discrete workflow module, enabling independent testing and future parallelization.

8. **Circuit breaker pattern** — Prevents cascading failures from external API outages; configurable threshold, recovery timeout, and half-open test requests.
