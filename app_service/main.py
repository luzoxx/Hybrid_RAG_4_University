from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from app.crawl_router import router as crawl_router
from app.chat_router import router as chat_router
from app.facebook_router import router as facebook_router
import uvicorn
import os
from dotenv import load_dotenv

# Tải các biến môi trường
load_dotenv()

# Khởi tạo FastAPI app
app = FastAPI(
    title="Đồ án tổng hợp API",
    description="API kết hợp crawl, chat và Facebook Messenger Webhook",
    version="1.0.0"
)

# Thêm các router
app.include_router(crawl_router)
app.include_router(chat_router)
app.include_router(facebook_router)

@app.get("/")
def read_root():
    return {"message": "Chào mừng đến với API. Sử dụng /crawl, /chat hoặc /facebook"}

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_redirect():
    return RedirectResponse(url="/docs")

# Xử lý chuyển hướng từ API crawl sang API chat
@app.middleware("http")
async def redirect_after_crawl(request: Request, call_next):
    response = await call_next(request)
    
    # Nếu là response từ endpoint crawl và có next_endpoint
    # Thì chuyển hướng người dùng sang endpoint đó
    if request.url.path == "/crawl/" and hasattr(response, "body"):
        try:
            import json
            response_body = json.loads(response.body.decode())
            
            if "next_endpoint" in response_body:
                # Trả về redirect response
                return RedirectResponse(url=response_body["next_endpoint"])
        except:
            pass
    
    return response

if __name__ == "__main__":
    # Lấy PORT từ biến môi trường hoặc sử dụng cổng mặc định
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
