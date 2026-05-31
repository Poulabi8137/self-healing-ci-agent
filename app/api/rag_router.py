from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.utils.logger import get_logger
from app.auth.dependencies import require_recruiter, require_admin
from app.rag.indexing_pipeline import index_repository
from app.rag.embedding import get_embedding_service
from app.rag.retriever import RetrieverService

logger = get_logger(__name__)

router = APIRouter()


class IndexRequest(BaseModel):
    repo_url: str = Field(..., max_length=500)
    branch: Optional[str] = Field(None, max_length=100)
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None


class RetrieveRequest(BaseModel):
    repo_name: str = Field(..., max_length=255)
    query: str = Field(..., max_length=500)
    top_k: int = Field(default=5, le=100)


@router.post("/index")
async def api_index_repository(req: IndexRequest, user=Depends(require_recruiter)):
    logger.info(f"Index request for {req.repo_url} (branch={req.branch})")
    try:
        result = index_repository(
            repo_url=req.repo_url,
            branch=req.branch,
            chunk_size=req.chunk_size,
            chunk_overlap=req.chunk_overlap,
        )
        logger.info(f"Indexing completed for {req.repo_url}")
        return result
    except Exception as e:
        logger.error(f"Indexing failed for {req.repo_url}: {str(e)}")
        raise HTTPException(status_code=500, detail="Indexing failed. Check server logs for details.")


@router.post("/retrieve")
async def api_retrieve(req: RetrieveRequest, user=Depends(require_recruiter)):
    logger.info(f"Retrieve request for {req.repo_name}: query='{req.query[:50]}...'")
    try:
        emb = get_embedding_service().get_embeddings()
        retriever = RetrieverService(emb)
        results = retriever.retrieve(
            query=req.query,
            repo_name=req.repo_name,
            top_k=req.top_k,
        )
        logger.info(f"Retrieved {len(results)} results for {req.repo_name}")
        return {
            "repo_name": req.repo_name,
            "query": req.query,
            "results": results,
            "count": len(results),
        }
    except Exception as e:
        logger.error(f"Retrieval failed for {req.repo_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Retrieval failed. Check server logs for details.")


@router.get("/index/{repo_name}/status")
async def api_index_status(repo_name: str, user=Depends(require_admin)):
    emb = get_embedding_service().get_embeddings()
    retriever = RetrieverService(emb)
    exists = retriever.index_exists(repo_name)
    logger.info(f"Index status for {repo_name}: {exists}")
    return {
        "repo_name": repo_name,
        "is_indexed": exists,
    }
