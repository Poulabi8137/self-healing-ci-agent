from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.utils.logger import get_logger
from app.rag.indexing_pipeline import index_repository
from app.rag.embedding import get_embedding_service
from app.rag.retriever import RetrieverService

logger = get_logger(__name__)

router = APIRouter()


class IndexRequest(BaseModel):
    repo_url: str
    branch: Optional[str] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None


class RetrieveRequest(BaseModel):
    repo_name: str
    query: str
    top_k: int = 5


@router.post("/index")
async def api_index_repository(req: IndexRequest):
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
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retrieve")
async def api_retrieve(req: RetrieveRequest):
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
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/index/{repo_name}/status")
async def api_index_status(repo_name: str):
    emb = get_embedding_service().get_embeddings()
    retriever = RetrieverService(emb)
    exists = retriever.index_exists(repo_name)
    logger.info(f"Index status for {repo_name}: {exists}")
    return {
        "repo_name": repo_name,
        "is_indexed": exists,
    }
