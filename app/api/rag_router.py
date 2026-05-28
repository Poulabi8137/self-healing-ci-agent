from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.rag.indexing_pipeline import index_repository
from app.rag.embedding import get_embedding_service
from app.rag.retriever import RetrieverService

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
    try:
        result = index_repository(
            repo_url=req.repo_url,
            branch=req.branch,
            chunk_size=req.chunk_size,
            chunk_overlap=req.chunk_overlap,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retrieve")
async def api_retrieve(req: RetrieveRequest):
    try:
        emb = get_embedding_service().get_embeddings()
        retriever = RetrieverService(emb)
        results = retriever.retrieve(
            query=req.query,
            repo_name=req.repo_name,
            top_k=req.top_k,
        )
        return {
            "repo_name": req.repo_name,
            "query": req.query,
            "results": results,
            "count": len(results),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/index/{repo_name}/status")
async def api_index_status(repo_name: str):
    emb = get_embedding_service().get_embeddings()
    retriever = RetrieverService(emb)
    exists = retriever.index_exists(repo_name)
    return {
        "repo_name": repo_name,
        "is_indexed": exists,
    }
