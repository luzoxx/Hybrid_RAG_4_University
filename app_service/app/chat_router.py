from fastapi import APIRouter, HTTPException
from models.chat_models import QueryRequest, QueryResponse
from services.chat_service import chat_service
import os

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)

@router.post("/qa", response_model=QueryResponse)
async def chat_qa(request: QueryRequest):
    try:
        # Sử dụng chat_service để xử lý
        result = chat_service.qa_system(
            query=request.query,
            search_method="hybrid",  # Cứng
            top_k=15,               # Cứng
            rerank_top_k=2,         # Cứng
            alpha=0.8               # Cứng
        )
        
        return QueryResponse(answer=result["answer"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý: {str(e)}")

@router.post("/vector")
async def vector_search(request: QueryRequest):
    try:
        # Sử dụng chat_service để xử lý với phương thức vector
        result = chat_service.qa_system(
            query=request.query,
            search_method="vector",  # Vector search
            top_k=15,
            rerank_top_k=5
        )
        
        return {"answer": result["answer"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tìm kiếm vector: {str(e)}")

@router.post("/elasticsearch")
async def elasticsearch_search(request: QueryRequest):
    try:
        # Sử dụng chat_service để xử lý với phương thức elasticsearch
        result = chat_service.qa_system(
            query=request.query,
            search_method="elasticsearch",  # Elasticsearch search
            top_k=15,
            rerank_top_k=5
        )
        
        return {"answer": result["answer"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tìm kiếm Elasticsearch: {str(e)}")

@router.post("/hybrid")
async def hybrid_search(request: QueryRequest):
    try:
        # Sử dụng chat_service để xử lý với phương thức hybrid
        result = chat_service.qa_system(
            query=request.query,
            search_method="hybrid",  # Hybrid search
            top_k=15,
            rerank_top_k=5,
            alpha=0.8
        )
        
        return {"answer": result["answer"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tìm kiếm hybrid: {str(e)}")

@router.get("/")
def read_chat_root():
    return {"message": "Chào mừng đến với API Chat"} 