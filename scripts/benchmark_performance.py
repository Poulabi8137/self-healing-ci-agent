"""Performance benchmark script.

Seeds the database with test data and measures dashboard endpoint latencies.
Run from project root: py -3.14 scripts/benchmark_performance.py
"""

import contextlib
import io
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.settings import settings
from app.database.db import SessionLocal, init_db, engine
from app.database.models import Base, RetryAttempt, ReviewResult, PRRecord
from app.dashboard.analytics_engine import (
    compute_full_analytics,
    compute_validation_pass_rate,
    compute_average_review_score,
    compute_average_confidence,
    compute_retry_distribution,
)
from app.dashboard.metrics_collector import collect_workflow_metrics, collect_repository_metrics
from app.dashboard.benchmark_service import get_benchmark_summary
from app.dashboard.charts import (
    get_success_vs_failure_dataset,
    get_retry_distribution_dataset,
    get_review_scores_dataset,
    get_validation_results_dataset,
    get_pr_statistics_dataset,
)
from app.dashboard.report_generator import generate_report


SEED_ROWS = 5000


def seed_database():
    """Populate the database with realistic test data."""
    print(f"Seeding database with ~{SEED_ROWS} rows per table...")
    db = SessionLocal()
    try:
        existing = db.query(RetryAttempt).count()
        if existing > 0:
            print(f"Database already has {existing} retry attempts — skipping seed")
            return

        repositories = [f"org/repo-{i}" for i in range(20)]
        statuses = ["passed", "failed"]
        recommendations = ["approved", "approved_with_warnings", "rejected"]

        start = time.time()

        batch = []
        for i in range(SEED_ROWS):
            repo = repositories[i % len(repositories)]
            status = statuses[i % 2] if i % 3 != 0 else statuses[(i + 1) % 2]
            batch.append(RetryAttempt(
                repository_name=repo,
                attempt_number=(i % 3) + 1,
                fix_summary=f"Fix for {repo} attempt {(i % 3) + 1}",
                validation_status=status,
                confidence_score=0.5 + (i % 5) * 0.1,
            ))

        for i in range(SEED_ROWS // 10):
            repo = repositories[i % len(repositories)]
            score = 0.5 + (i % 5) * 0.1
            batch.append(ReviewResult(
                repository_name=repo,
                overall_score=min(score, 1.0),
                recommendation=recommendations[i % len(recommendations)],
            ))

        for i in range(SEED_ROWS // 20):
            repo = repositories[i % len(repositories)]
            batch.append(PRRecord(
                repository_name=repo,
                branch_name=f"fix/attempt-{i}",
                pr_title=f"Fix for {repo}",
                status="simulated" if i % 2 == 0 else "real",
                dry_run=(i % 2 == 0),
            ))

        for obj in batch:
            db.add(obj)
        db.commit()

        elapsed = time.time() - start
        print(f"Seeded {len(batch)} records in {elapsed:.2f}s")

        counts = {
            "retry_attempts": db.query(RetryAttempt).count(),
            "review_results": db.query(ReviewResult).count(),
            "pr_records": db.query(PRRecord).count(),
        }
        for table, count in counts.items():
            print(f"  {table}: {count} rows")
    finally:
        db.close()


def measure(label, func, *args, **kwargs):
    """Measure function execution time, return (result, elapsed_ms)."""
    with contextlib.suppress(Exception):
        pass

    start = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed = (time.perf_counter() - start) * 1000
    print(f"  {label}: {elapsed:.1f}ms")
    return result, elapsed


def main():
    print("=" * 60)
    print("Performance Benchmark")
    print("=" * 60)

    init_db()
    seed_database()

    print("\n--- Dashboard Endpoint Latency ---")

    results = {}

    # Warm up — first call populates cache
    print("\n[Warm-up: cold cache]")
    results["cold"] = {}
    for label, func in [
        ("collect_workflow_metrics", collect_workflow_metrics),
        ("collect_repository_metrics", collect_repository_metrics),
        ("compute_full_analytics", compute_full_analytics),
        ("get_benchmark_summary", get_benchmark_summary),
        ("generate_report (full)", lambda: generate_report("full")),
        ("generate_report (summary)", lambda: generate_report("summary")),
        ("get_success_vs_failure", get_success_vs_failure_dataset),
        ("get_retry_distribution_dataset", get_retry_distribution_dataset),
        ("get_review_scores_dataset", get_review_scores_dataset),
        ("get_validation_results_dataset", get_validation_results_dataset),
        ("get_pr_statistics_dataset", get_pr_statistics_dataset),
    ]:
        _, elapsed = measure(label, func)
        results["cold"][label] = elapsed

    # Cached — second call uses TTL cache
    print("\n[Cached: hot cache]")
    results["cached"] = {}
    for label, func in [
        ("collect_workflow_metrics", collect_workflow_metrics),
        ("collect_repository_metrics", collect_repository_metrics),
        ("compute_full_analytics", compute_full_analytics),
        ("get_benchmark_summary", get_benchmark_summary),
        ("generate_report (full)", lambda: generate_report("full")),
        ("get_success_vs_failure", get_success_vs_failure_dataset),
        ("get_pr_statistics_dataset", get_pr_statistics_dataset),
    ]:
        _, elapsed = measure(label, func)
        results["cached"][label] = elapsed

    # Disk-backed: wait for cache expiry, then measure without warming
    print("\n[Disk-backed: uncached, SQLite I/O]")
    from app.utils.cache import ttl_cache
    collect_workflow_metrics.invalidate()
    collect_repository_metrics.invalidate()
    compute_full_analytics.invalidate()

    results["uncached"] = {}
    for label, func in [
        ("collect_workflow_metrics", collect_workflow_metrics),
        ("collect_repository_metrics", collect_repository_metrics),
        ("compute_full_analytics", compute_full_analytics),
    ]:
        _, elapsed = measure(label, func)
        results["uncached"][label] = elapsed

    # Individual analytics functions
    print("\n--- Individual Analytics Functions (uncached) ---")
    analytics_results = {}
    for label, func in [
        ("compute_validation_pass_rate", compute_validation_pass_rate),
        ("compute_average_review_score", compute_average_review_score),
        ("compute_average_confidence", compute_average_confidence),
        ("compute_retry_distribution", compute_retry_distribution),
    ]:
        _, elapsed = measure(label, func)
        analytics_results[label] = elapsed

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    def avg(vals):
        return sum(vals) / len(vals) if vals else 0

    cold_times = [v for v in results["cold"].values()]
    cached_times = [v for v in results["cached"].values()]
    print(f"Cold cache avg:  {avg(cold_times):.1f}ms")
    print(f"Hot cache avg:   {avg(cached_times):.1f}ms")
    print(f"Improvement:     {avg(cold_times)/max(avg(cached_times),0.1):.1f}x faster")

    print(f"\nUncached DB avg: {avg(results['uncached'].values()):.1f}ms")
    print(f"Analytics avg:   {avg(analytics_results.values()):.1f}ms")

    return results, analytics_results


if __name__ == "__main__":
    main()
