from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from models.crawl_models import CrawlRequest, CrawlResponse
from services.crawl_service import crawl_service

router = APIRouter(
    prefix="/crawl",
    tags=["crawl"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=CrawlResponse)
async def crawl_data(request: CrawlRequest, req: Request):
    if not request.state:
        # Nếu state = False, chuyển hướng ngay sang API chat
        return CrawlResponse(
            status="success",
            message="Chuyển hướng sang API chat",
            next_endpoint="/chat/qa"
        )
    
    try:
        # Xử lý crawl dữ liệu
        result = crawl_service.process_crawl(request.username, request.password)
        
        # Sau khi xử lý, luôn chuyển hướng sang API chat
        return CrawlResponse(
            status=result["status"],
            message=result["message"],
            data=result["data"],
            next_endpoint="/chat/qa"  # Luôn chuyển hướng sang API chat
        )
    except Exception as e:
        # Nếu có lỗi, vẫn chuyển hướng sang API chat
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi xử lý yêu cầu: {str(e)}"
        ) 