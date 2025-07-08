from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse, PlainTextResponse
from models.facebook_models import FacebookVerification, FacebookWebhookEvent
from services.facebook_service import facebook_service
from services.crawl_service import crawl_service
import requests
import json

router = APIRouter(
    prefix="/facebook",
    tags=["facebook"],
    responses={404: {"description": "Not found"}},
)

@router.get("/webhook")
async def verify_webhook(hub_mode: str, hub_verify_token: str, hub_challenge: str):
    """
    Xử lý xác thực webhook từ Facebook
    """
    # Xác thực webhook
    challenge = facebook_service.verify_webhook(hub_mode, hub_verify_token, hub_challenge)
    
    if challenge:
        # Trả về hub.challenge để xác thực thành công
        return PlainTextResponse(content=challenge)
    else:
        # Xác thực thất bại
        raise HTTPException(status_code=403, detail="Xác thực webhook thất bại")

@router.post("/webhook")
async def process_webhook(request: Request):
    """
    Xử lý sự kiện webhook từ Facebook
    """
    # Đọc body của request
    body = await request.json()
    
    # Phân tích cú pháp để xác định hành động
    try:
        responses = []
        processed_responses = facebook_service.process_webhook_event(body)
        
        # Xử lý từng response
        for response_data in processed_responses:
            if isinstance(response_data, dict) and "recipient" in response_data and "message" in response_data:
                # Nếu cần gọi API chat hoặc crawl
                if response_data.get("requires_api_call"):
                    
                    recipient_id = response_data["recipient"]["id"]
                    action = response_data.get("action")
                    
                    if action == "chat":
                        query = response_data.get("query", "")
                        chat_responses = await facebook_service._call_chat_api(recipient_id, query)
                        responses.extend(chat_responses)
                    
                    elif action == "crawl":
                        crawl_responses = await facebook_service._call_crawl_api(recipient_id)
                        responses.extend(crawl_responses)
                
                else:
                    # Đây là tin nhắn thông thường
                    responses.append(response_data)
    
    except Exception as e:
        # Trả về 200 OK để Facebook biết chúng ta đã nhận được webhook
        # nhưng log lỗi
        print(f"Lỗi khi xử lý webhook: {str(e)}")
        return JSONResponse(content={"status": "error", "message": str(e)})
    
    # Gửi tin nhắn phản hồi đến Facebook
    for response in responses:
        facebook_service.send_message(response)
    
    # Trả về 200 OK để Facebook biết chúng ta đã nhận được webhook
    return JSONResponse(content={"status": "ok"})

@router.post("/send-message")
async def send_message(recipient_id: str, message: str):
    """
    API gửi tin nhắn đến người dùng Facebook
    """
    message_data = facebook_service._create_text_message(recipient_id, message)
    result = facebook_service.send_message(message_data)
    
    return JSONResponse(content=result)

@router.get("/setup")
async def setup_messenger():
    """
    API thiết lập các tính năng của Messenger (Get Started button, Persistent Menu)
    """
    # Lấy token từ biến môi trường
    page_access_token = facebook_service.page_access_token
    
    # Thiết lập Get Started button
    get_started_url = f"https://graph.facebook.com/v18.0/me/messenger_profile?access_token={page_access_token}"
    get_started_data = {
        "get_started": {
            "payload": "GET_STARTED"
        }
    }
    
    get_started_response = requests.post(
        get_started_url,
        headers={"Content-Type": "application/json"},
        data=json.dumps(get_started_data)
    )
    
    # Thiết lập Persistent Menu
    persistent_menu_url = f"https://graph.facebook.com/v18.0/me/messenger_profile?access_token={page_access_token}"
    persistent_menu_data = {
        "persistent_menu": [
            {
                "locale": "default",
                "composer_input_disabled": False,
                "call_to_actions": [
                    {
                        "type": "postback",
                        "title": "Bắt đầu lại",
                        "payload": "GET_STARTED"
                    },
                    {
                        "type": "postback",
                        "title": "Trợ giúp",
                        "payload": "HELP"
                    }
                ]
            }
        ]
    }
    
    persistent_menu_response = requests.post(
        persistent_menu_url,
        headers={"Content-Type": "application/json"},
        data=json.dumps(persistent_menu_data)
    )
    
    return JSONResponse(content={
        "get_started": get_started_response.json(),
        "persistent_menu": persistent_menu_response.json()
    }) 