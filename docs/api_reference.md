# API Reference

## Base URL

`http://localhost:8000`

Interactive docs available at `http://localhost:8000/docs` (Swagger UI).

---

## System Endpoints

### `GET /health`

Health check endpoint.

**Response 200:**
```json
{
  "status": "healthy",
  "timestamp": "2026-06-02T10:30:00.123456"
}
```

### `GET /version`

Application version information.

**Response 200:**
```json
{
  "app_name": "Self-Healing AI CI/CD Agent",
  "version": "1.0.0"
}
```

---

## RAG Endpoints (`/rag`)

### `POST /rag/index`

Index a repository for RAG-based context retrieval.

**Request:**
```json
{
  "repo_url": "https://github.com/user/repo",
  "branch": "main",
  "chunk_size": 512,
  "chunk_overlap": 50
}
```

**Response 200:**
```json
{
  "repo_name": "user/repo",
  "status": "indexed",
  "chunks_count": 42,
  "index_path": "/app/data/vector_store/user_repo"
}
```

### `POST /rag/retrieve`

Retrieve relevant context for a query.

**Request:**
```json
{
  "repo_name": "user/repo",
  "query": "database connection pooling",
  "top_k": 5
}
```

**Response 200:**
```json
{
  "repo_name": "user/repo",
  "query": "database connection pooling",
  "results": [
    {
      "content": "def create_pool(): ...",
      "metadata": {
        "file_path": "src/db.py",
        "chunk_id": 3,
        "score": 0.92
      }
    }
  ],
  "count": 5
}
```

### `GET /rag/index/{repo_name}/status`

Check if a repository has been indexed.

**Response 200:**
```json
{
  "repo_name": "user/repo",
  "is_indexed": true
}
```

---

## Analysis Endpoints (`/analysis`)

### `POST /analysis/debug`

Analyze CI/CD failure logs and identify root cause.

**Request:**
```json
{
  "repository_name": "my-org-my-repo",
  "logs": "ERROR: pytest failed\ntest_api.py:42: AssertionError\nExpected 200, got 500"
}
```

**Response 200:**
```json
{
  "repository_name": "my-org-my-repo",
  "error_summary": "API test failure: test_api.py line 42",
  "error_category": "test_failure",
  "root_cause": "Missing error handling in /api/v1/users endpoint",
  "context": [
    {
      "file": "app/routes/users.py",
      "snippet": "@router.get('/users') ..."
    }
  ],
  "suggested_approach": "Add try-except block to handle database timeout"
}
```

---

## Fix Endpoints (`/fix`)

### `POST /fix/generate`

Generate an AI-powered fix for a CI/CD failure.

**Request:**
```json
{
  "repository_name": "my-org-my-repo",
  "logs": "ERROR: pytest failed\ntest_api.py:42: AssertionError"
}
```

**Response 200:**
```json
{
  "repository_name": "my-org-my-repo",
  "fix_summary": "Added error handling to /api/v1/users endpoint",
  "modified_files": [
    {
      "path": "app/routes/users.py",
      "changes": "Added try-except for database timeout"
    }
  ],
  "patch": "--- a/app/routes/users.py\n+++ b/app/routes/users.py\n@@ -10,6 +10,7 @@\n     try:\n         users = get_users()\n+    except TimeoutError:\n+        return JSONResponse(status_code=500, detail='Database timeout')\n     return users",
  "assumptions": [
    "The database timeout occurs under high load",
    "A 500 response is preferred over crashing"
  ]
}
```

---

## Validation Endpoints (`/validation`)

### `POST /validation/run`

Run the full validation pipeline on a fix.

**Request:**
```json
{
  "repository_name": "my-org-my-repo",
  "logs": "CI/CD failure logs..."
}
```

**Response 200:**
```json
{
  "repository_name": "my-org-my-repo",
  "syntax_valid": true,
  "syntax_errors": [],
  "build_valid": true,
  "build_errors": [],
  "tests_passed": 42,
  "tests_failed": 0,
  "overall_status": "passed",
  "details": {
    "syntax": { "status": "passed", "errors": [] },
    "build": { "status": "passed", "errors": [] },
    "test": { "status": "passed", "passed": 42, "failed": 0 }
  }
}
```

---

## Retry Endpoints (`/retry`)

### `POST /retry/run`

Run the self-healing retry workflow.

**Request:**
```json
{
  "repository_name": "my-org-my-repo",
  "logs": "CI/CD failure logs..."
}
```

**Response 200:**
```json
{
  "repository_name": "my-org-my-repo",
  "attempts": [
    {
      "attempt_number": 1,
      "status": "failed_validation",
      "fix_summary": "Initial fix attempt",
      "validation_status": "syntax_error"
    },
    {
      "attempt_number": 2,
      "status": "resolved",
      "fix_summary": "Fixed import path and syntax",
      "validation_status": "passed"
    }
  ],
  "total_attempts": 2,
  "final_status": "resolved",
  "final_fix": {
    "fix_summary": "Fixed import path and syntax",
    "modified_files": ["app/routes/users.py"],
    "confidence_score": 0.85
  }
}
```

---

## Review Endpoints (`/review`)

### `POST /review/run`

Run multi-agent review on a fix.

**Request:**
```json
{
  "repository_name": "my-org-my-repo",
  "logs": "CI/CD failure logs..."
}
```

**Response 200:**
```json
{
  "repository_name": "my-org-my-repo",
  "scores": {
    "security": 0.9,
    "performance": 0.85,
    "quality": 0.92,
    "coverage": 0.78
  },
  "overall_score": 0.86,
  "recommendation": "approved",
  "details": {
    "security": {
      "score": 0.9,
      "findings": ["No unsafe eval usage", "Input sanitization present"],
      "issues": []
    },
    "performance": {
      "score": 0.85,
      "findings": ["Acceptable query pattern"],
      "issues": ["N+1 query detected in loop"]
    },
    "quality": {
      "score": 0.92,
      "findings": ["Clean code structure"],
      "issues": []
    },
    "coverage": {
      "score": 0.78,
      "findings": ["New code has tests"],
      "issues": ["Edge case: empty result not tested"]
    }
  }
}
```

---

## PR Endpoints (`/pr`)

### `POST /pr/create`

Create a pull request with the generated fix.

**Request:**
```json
{
  "repository_name": "my-org-my-repo",
  "logs": "CI/CD failure logs...",
  "dry_run": true,
  "approved": false
}
```

**Response 200:**
```json
{
  "repository_name": "my-org-my-repo",
  "branch_name": "fix/api-error-handling-170533",
  "commit_message": "fix: Add error handling to /api/v1/users endpoint",
  "pr_title": "fix: Add error handling to /api/v1/users endpoint",
  "pr_description": "## Summary\n\nAdded error handling to address CI/CD failure...",
  "pr_url": "",
  "dry_run": true,
  "status": "simulated"
}
```

For a real PR (`dry_run: false`, `approved: true`):
```json
{
  "repository_name": "my-org-my-repo",
  "branch_name": "fix/api-error-handling-170533",
  "pr_url": "https://github.com/my-org/my-repo/pull/42",
  "dry_run": false,
  "status": "created"
}
```

---

## Dashboard Endpoints (`/dashboard`)

### `GET /dashboard/summary`

Get system-wide benchmark summary.

**Response 200:**
```json
{
  "system_health": {
    "total_workflow_runs": 150,
    "overall_success_rate": 85.3,
    "average_retries_per_run": 1.2
  },
  "validation": {
    "pass_rate": 94.0,
    "total_attempts": 160
  },
  "review": {
    "average_score": 0.86,
    "total_reviews": 45
  },
  "confidence": {
    "overall_confidence": 0.82,
    "average_confidence": 0.78
  },
  "repositories": [
    {
      "name": "my-org-my-repo",
      "runs": 30,
      "success_rate": 90.0
    }
  ]
}
```

### `GET /dashboard/metrics`

Get full analytics data.

**Response 200:**
```json
{
  "workflow_metrics": {
    "total_runs": 150,
    "total_successful": 128,
    "total_failed": 22,
    "total_retries": 35,
    "total_reviews": 45,
    "total_prs": 30,
    "total_prs_real": 12,
    "total_prs_simulated": 18
  },
  "repository_metrics": [
    {
      "repository_name": "my-org-my-repo",
      "total_runs": 30,
      "successful_runs": 27,
      "failed_runs": 3,
      "avg_confidence": 0.82,
      "success_rate": 90.0
    }
  ],
  "success_rate": 85.3,
  "average_retries": 0.23,
  "validation_pass_rate": 94.0,
  "average_review_score": 0.86,
  "average_confidence": 0.78,
  "retry_distribution": { "1": 20, "2": 10, "3": 5 },
  "total_repositories": 5
}
```

### `GET /dashboard/repositories`

Get per-repository metrics.

**Response 200:**
```json
[
  {
    "repository_name": "my-org-my-repo",
    "total_runs": 30,
    "successful_runs": 27,
    "failed_runs": 3,
    "avg_confidence": 0.82,
    "success_rate": 90.0
  }
]
```

### `GET /dashboard/reports?report_type=full`

Get structured benchmark report. Types: `full`, `summary`, `repositories`.

**Response 200:**
```json
{
  "report_type": "full",
  "generated_at": "2025-01-15T10:30:00.123456",
  "system_version": "0.1.0",
  "overview": {
    "total_runs": 150,
    "success_rate": 85.3,
    "average_retries": 1.2,
    "average_confidence": 0.78
  },
  "validation": {
    "pass_rate": 94.0,
    "total_attempts": 160
  },
  "review": {
    "average_score": 0.86,
    "total_reviews": 45
  },
  "pr": {
    "total_prs": 30,
    "real_prs": 12,
    "simulated_prs": 18
  },
  "repositories": [],
  "retry_distribution": {}
}
```

### `GET /dashboard/charts/success-failure`

Success vs failure comparison dataset.

**Response 200:**
```json
{
  "labels": ["Successful", "Failed"],
  "values": [128, 22],
  "colors": ["#28a745", "#dc3545"]
}
```

### `GET /dashboard/charts/retry-distribution`

Retry attempt distribution dataset.

**Response 200:**
```json
{
  "labels": ["Attempt 1", "Attempt 2", "Attempt 3"],
  "values": [20, 10, 5]
}
```

### `GET /dashboard/charts/review-scores`

Review scores by category.

**Response 200:**
```json
{
  "categories": ["Security", "Performance", "Quality", "Coverage", "Overall"],
  "scores": [0.86, 0.86, 0.86, 0.86, 0.86],
  "average": 0.86
}
```

### `GET /dashboard/charts/validation-results`

Validation pass/fail rates.

**Response 200:**
```json
{
  "labels": ["Passed", "Failed"],
  "values": [94.0, 6.0]
}
```

### `GET /dashboard/charts/pr-statistics`

PR statistics (simulated vs real).

**Response 200:**
```json
{
  "labels": ["Simulated PRs", "Real PRs"],
  "values": [18, 12]
}
```

---

## Error Responses

All endpoints return consistent error format on failure:

```json
{
  "detail": "Error description message"
}
```

| Status Code | Meaning |
|-------------|---------|
| 200 | Success |
| 422 | Validation Error (invalid request body) |
| 500 | Internal Server Error |
