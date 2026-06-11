from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text

from app.database.db import Base


class User(Base):
    """User accounts from Google OAuth."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    google_id = Column(String(255), unique=True, nullable=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255))
    avatar_url = Column(String(500))
    role = Column(String(32), nullable=False, default="member")
    github_id = Column(Integer, nullable=True, unique=True)
    github_username = Column(String(255), nullable=True)
    github_email = Column(String(255), nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False, unique=True)
    url = Column(String(500))
    default_branch = Column(String(100), default="main")
    is_active = Column(Boolean, default=True)
    last_workflow_status = Column(String(50), nullable=True)
    last_workflow_run_at = Column(DateTime, nullable=True)
    failure_count = Column(Integer, default=0)
    is_indexed = Column(Boolean, default=False)
    indexed_at = Column(DateTime, nullable=True)
    chunks_count = Column(Integer, default=0)
    github_installation_id = Column(Integer, ForeignKey("github_installations.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Repository(id={self.id}, name='{self.full_name}')>"


class Failure(Base):
    __tablename__ = "failures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repository_id = Column(Integer, nullable=False)
    github_installation_id = Column(Integer, nullable=True)
    investigation_id = Column(Integer, nullable=True)
    workflow_name = Column(String(255))
    run_id = Column(String(255))
    job_name = Column(String(255))
    step_name = Column(String(255))
    error_message = Column(Text)
    error_logs = Column(Text)
    status = Column(String(50), default="detected")
    detected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Failure(id={self.id}, repo_id={self.repository_id}, status='{self.status}')>"


class Fix(Base):
    __tablename__ = "fixes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    failure_id = Column(Integer, nullable=False)
    suggested_fix = Column(Text)
    applied_fix = Column(Text)
    fix_type = Column(String(50), default="auto")
    status = Column(String(50), default="suggested")
    confidence_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    applied_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Fix(id={self.id}, failure_id={self.failure_id}, status='{self.status}')>"


class RetryAttempt(Base):
    __tablename__ = "retry_attempts"

    __table_args__ = (
        Index("idx_retry_repo_status_conf", "repository_name", "validation_status", "confidence_score"),
        Index("idx_retry_attempt_number", "attempt_number"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    repository_name = Column(String(255), nullable=False)
    attempt_number = Column(Integer, nullable=False)
    fix_summary = Column(Text)
    validation_status = Column(String(50), default="unknown")
    confidence_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<RetryAttempt(id={self.id}, repo='{self.repository_name}', attempt={self.attempt_number}, status='{self.validation_status}')>"


class ReviewResult(Base):
    __tablename__ = "review_results"

    __table_args__ = (
        Index("idx_review_repo", "repository_name"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    repository_name = Column(String(255), nullable=False)
    overall_score = Column(Float, default=0.0)
    recommendation = Column(String(50), default="pending")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<ReviewResult(id={self.id}, repo='{self.repository_name}', score={self.overall_score}, rec='{self.recommendation}')>"


class PRRecord(Base):
    __tablename__ = "pr_records"

    __table_args__ = (
        Index("idx_pr_repo", "repository_name"),
        Index("idx_pr_dry_run", "dry_run"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    repository_name = Column(String(255), nullable=False)
    branch_name = Column(String(255))
    pr_title = Column(Text)
    status = Column(String(50), default="simulated")
    dry_run = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<PRRecord(id={self.id}, repo='{self.repository_name}', status='{self.status}', dry_run={self.dry_run})>"


class BenchmarkRun(Base):
    __tablename__ = "benchmark_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repository_name = Column(String(255), nullable=False)
    total_attempts = Column(Integer, default=0)
    successful_attempts = Column(Integer, default=0)
    failed_attempts = Column(Integer, default=0)
    avg_confidence = Column(Float, default=0.0)
    validation_pass_rate = Column(Float, default=0.0)
    avg_review_score = Column(Float, default=0.0)
    pr_created = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<BenchmarkRun(id={self.id}, repo='{self.repository_name}', attempts={self.total_attempts})>"


class RepositoryMetrics(Base):
    __tablename__ = "repository_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repository_name = Column(String(255), nullable=False, unique=True)
    total_runs = Column(Integer, default=0)
    total_retries = Column(Integer, default=0)
    avg_retries_per_run = Column(Float, default=0.0)
    success_rate = Column(Float, default=0.0)
    avg_confidence = Column(Float, default=0.0)
    last_run_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<RepoMetrics(id={self.id}, repo='{self.repository_name}', rate={self.success_rate})>"


class WorkflowMetrics(Base):
    __tablename__ = "workflow_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_type = Column(String(100), nullable=False)
    total_runs = Column(Integer, default=0)
    successful_runs = Column(Integer, default=0)
    failed_runs = Column(Integer, default=0)
    avg_duration_seconds = Column(Float, default=0.0)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<WorkflowMetrics(id={self.id}, type='{self.workflow_type}', runs={self.total_runs})>"


class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repository_id = Column(Integer, nullable=False)
    total_failures = Column(Integer, default=0)
    auto_fixes = Column(Integer, default=0)
    manual_fixes = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    avg_resolution_time = Column(Float, default=0.0)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Metric(id={self.id}, repo_id={self.repository_id})>"


class GitHubInstallation(Base):
    """GitHub App installations per user."""
    __tablename__ = "github_installations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    installation_id = Column(Integer, nullable=False, unique=True)
    account_login = Column(String(255))
    account_type = Column(String(50))
    account_avatar = Column(String(500))
    account_url = Column(String(500), nullable=True)
    github_id = Column(Integer, nullable=True)
    repos_selected = Column(Text, default="[]")
    token_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<GitHubInstallation(id={self.id}, account='{self.account_login}', install={self.installation_id})>"


class WebhookEvent(Base):
    """Incoming GitHub webhook event log."""
    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    delivery_id = Column(String(255), nullable=True, unique=True)
    github_installation_id = Column(Integer, nullable=True)
    event_type = Column(String(100))
    action = Column(String(100), nullable=True)
    payload = Column(Text, default="{}")
    processed = Column(Boolean, default=False)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    processed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<WebhookEvent(id={self.id}, type='{self.event_type}', processed={self.processed})>"


class Investigation(Base):
    """Investigation tracking with JSON stages."""
    __tablename__ = "investigations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    failure_id = Column(Integer, ForeignKey("failures.id"), nullable=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=True)
    status = Column(String(50), default="detecting")
    root_cause = Column(Text, nullable=True)
    error_category = Column(String(100), nullable=True)
    confidence = Column(Float, nullable=True)
    summary = Column(Text, nullable=True)
    stages = Column(Text, default="[]")
    current_stage = Column(String(100), nullable=True)
    current_stage_status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Investigation(id={self.id}, status='{self.status}')>"


class AuditLog(Base):
    """Security-relevant action log."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(String(100), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', user_id={self.user_id})>"


class InvestigationEvent(Base):
    """Structured investigation lifecycle events for future consumers (SSE, Slack, etc.)."""
    __tablename__ = "investigation_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    investigation_id = Column(Integer, ForeignKey("investigations.id"), nullable=True)
    event_type = Column(String(100), nullable=False)
    data = Column(Text, default="{}")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<InvestigationEvent(id={self.id}, type='{self.event_type}', investigation_id={self.investigation_id})>"
