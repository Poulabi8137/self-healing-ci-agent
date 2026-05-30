import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Index, Integer, String, Text

from app.database.db import Base


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False, unique=True)
    url = Column(String(500))
    default_branch = Column(String(100), default="main")
    is_indexed = Column(Boolean, default=False)
    indexed_at = Column(DateTime, nullable=True)
    chunks_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<Repository(id={self.id}, name='{self.full_name}')>"


class Failure(Base):
    __tablename__ = "failures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repository_id = Column(Integer, nullable=False)
    workflow_name = Column(String(255))
    run_id = Column(String(255))
    job_name = Column(String(255))
    step_name = Column(String(255))
    error_message = Column(Text)
    error_logs = Column(Text)
    status = Column(String(50), default="detected")
    detected_at = Column(DateTime, default=datetime.datetime.utcnow)
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
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
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
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

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
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

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
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

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
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

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
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

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
    recorded_at = Column(DateTime, default=datetime.datetime.utcnow)

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
    recorded_at = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<Metric(id={self.id}, repo_id={self.repository_id})>"
