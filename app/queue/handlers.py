from app.queue.worker import register_handler
from app.workflows.analysis_workflow import run_analysis
from app.workflows.fix_generation_workflow import run_fix_generation
from app.workflows.validation_workflow import run_validation_pipeline
from app.workflows.retry_workflow import run_retry_workflow
from app.workflows.review_workflow import run_review_workflow
from app.workflows.pr_workflow import run_pr_workflow


@register_handler("analysis")
async def handle_analysis(repository_name: str, logs: str):
    return await run_analysis(repository_name=repository_name, logs=logs)


@register_handler("fix")
async def handle_fix(repository_name: str, logs: str):
    return await run_fix_generation(repository_name=repository_name, logs=logs)


@register_handler("validation")
async def handle_validation(repository_name: str, logs: str):
    return await run_validation_pipeline(repository_name=repository_name, logs=logs)


@register_handler("retry")
async def handle_retry(repository_name: str, logs: str):
    return await run_retry_workflow(repository_name=repository_name, logs=logs)


@register_handler("review")
async def handle_review(repository_name: str, logs: str):
    return await run_review_workflow(repository_name=repository_name, logs=logs)


@register_handler("pr_create")
async def handle_pr_create(repository_name: str, logs: str, dry_run: bool = True, approved: bool = False):
    return await run_pr_workflow(
        repository_name=repository_name,
        logs=logs,
        dry_run=dry_run,
        approved=approved,
    )


@register_handler("rag_index")
async def handle_rag_index(repo_url: str, branch: str = None, chunk_size: int = None, chunk_overlap: int = None):
    from app.rag.indexing_pipeline import index_repository
    return index_repository(repo_url=repo_url, branch=branch, chunk_size=chunk_size, chunk_overlap=chunk_overlap)


@register_handler("rag_retrieve")
async def handle_rag_retrieve(repo_name: str, query: str, top_k: int = 5):
    from app.rag.embedding import get_embedding_service
    from app.rag.retriever import RetrieverService
    emb = get_embedding_service().get_embeddings()
    retriever = RetrieverService(emb)
    results = retriever.retrieve(query=query, repo_name=repo_name, top_k=top_k)
    return {"repo_name": repo_name, "query": query, "results": results, "count": len(results)}


def register_all_handlers():
    pass  # imports above trigger @register_handler decorators
