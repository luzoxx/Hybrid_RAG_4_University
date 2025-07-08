import requests
import json
import os
from typing import Dict, Any, Optional, List
from services.crawl_service import crawl_service
import httpx

# Lưu trạng thái người dùng
user_states = {}

# Các trạng thái
class UserState:
    INITIAL = "initial"
    WAITING_USERNAME = "waiting_username"
    WAITING_PASSWORD = "waiting_password"
    CHATTING = "chatting"

class FacebookService:
    def __init__(self):
        # Lấy token từ biến môi trường
        self.page_access_token = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN", "your_facebook_page_access_token")
        self.verify_token = os.environ.get("FACEBOOK_VERIFY_TOKEN", "your_verify_token")
        self.api_url = "https://graph.facebook.com/v18.0/me/messages"
        
        # URL của API chat và crawl
        self.base_url = os.environ.get("BASE_URL", "http://localhost:8000")
        self.chat_url = f"{self.base_url}/chat/qa"
        self.crawl_url = f"{self.base_url}/crawl/"
        
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """
        Xác thực webhook khi Facebook gửi GET request
        """
        if mode == "subscribe" and token == self.verify_token:
            return challenge
        return None
    
    def process_webhook_event(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Xử lý sự kiện webhook từ Facebook
        """
        responses = []
        
        if event["object"] == "page":
            for entry in event["entry"]:
                for messaging in entry["messaging"]:
                    sender_id = messaging["sender"]["id"]
                    
                    # Khởi tạo trạng thái nếu chưa có
                    if sender_id not in user_states:
                        user_states[sender_id] = {
                            "state": UserState.INITIAL,
                            "data": {}
                        }
                    
                    # Xử lý postback
                    if "postback" in messaging:
                        responses.extend(self._handle_postback(sender_id, messaging["postback"]))
                    
                    # Xử lý tin nhắn thông thường
                    elif "message" in messaging:
                        if "quick_reply" in messaging["message"]:
                            responses.extend(self._handle_quick_reply(sender_id, messaging["message"]["quick_reply"]))
                        else:
                            responses.extend(self._handle_message(sender_id, messaging["message"]))
        
        return responses
    
    def _handle_postback(self, sender_id: str, postback: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Xử lý postback từ người dùng
        """
        payload = postback["payload"]
        
        if payload == "GET_STARTED":
            return self._send_welcome_message(sender_id)
        elif payload == "HELP":
            return [self._create_text_message(sender_id, "Bạn có thể đăng nhập và đặt câu hỏi với tôi. Tôi sẽ cố gắng trả lời bạn.")]
        
        return []
    
    def _handle_quick_reply(self, sender_id: str, quick_reply: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Xử lý quick reply từ người dùng
        """
        payload = quick_reply["payload"]
        
        if payload == "LOGIN_YES":
            # Chuyển sang trạng thái đợi username
            user_states[sender_id]["state"] = UserState.WAITING_USERNAME
            return [self._create_text_message(sender_id, "Vui lòng nhập username của bạn:")]
        
        elif payload == "LOGIN_NO":
            # Gọi trực tiếp API chat
            user_states[sender_id]["state"] = UserState.CHATTING
            return self._redirect_to_chat(sender_id)
        
        return []
    
    def _handle_message(self, sender_id: str, message: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Xử lý tin nhắn thông thường từ người dùng
        """
        if "text" not in message:
            return [self._create_text_message(sender_id, "Tôi không hiểu tin nhắn này. Vui lòng gửi tin nhắn văn bản.")]
        
        text = message["text"]
        user_state = user_states[sender_id]["state"]
        
        if user_state == UserState.INITIAL:
            # Gửi tin nhắn chào mừng với các nút Quick Reply
            return self._send_welcome_message(sender_id)
        
        elif user_state == UserState.WAITING_USERNAME:
            # Lưu username và chuyển sang trạng thái đợi password
            user_states[sender_id]["data"]["username"] = text
            user_states[sender_id]["state"] = UserState.WAITING_PASSWORD
            return [self._create_text_message(sender_id, "Vui lòng nhập password của bạn:")]
        
        elif user_state == UserState.WAITING_PASSWORD:
            # Lưu password và gọi API crawl
            user_states[sender_id]["data"]["password"] = text
            # Trả về một response yêu cầu gọi API crawl
            return [{
                "recipient": {"id": sender_id},
                "message": {"text": f"Đang xử lý đăng nhập với username: {text}... Vui lòng đợi."},
                "requires_api_call": True,
                "action": "crawl"
            }]
        
        elif user_state == UserState.CHATTING:
            # Gọi API chat với tin nhắn của người dùng
            return [{
                "recipient": {"id": sender_id},
                "message": {"text": "Đang xử lý câu hỏi của bạn... Vui lòng đợi."},
                "requires_api_call": True,
                "action": "chat",
                "query": text
            }]
        
        else:
            # Gọi API chat với tin nhắn của người dùng
            user_states[sender_id]["state"] = UserState.CHATTING
            return [{
                "recipient": {"id": sender_id},
                "message": {"text": "Đang xử lý câu hỏi của bạn... Vui lòng đợi."},
                "requires_api_call": True,
                "action": "chat",
                "query": text
            }]
    
    def _send_welcome_message(self, sender_id: str) -> List[Dict[str, Any]]:
        """
        Gửi tin nhắn chào mừng với các nút Quick Reply
        """
        return [{
            "recipient": {"id": sender_id},
            "message": {
                "text": "Xin chào! Bạn muốn đăng nhập không?",
                "quick_replies": [
                    {
                        "content_type": "text",
                        "title": "Có",
                        "payload": "LOGIN_YES"
                    },
                    {
                        "content_type": "text",
                        "title": "Không",
                        "payload": "LOGIN_NO"
                    }
                ]
            }
        }]
    
    async def _call_crawl_api(self, sender_id: str) -> List[Dict[str, Any]]:
        """
        Gọi API crawl với thông tin đăng nhập của người dùng
        """
        username = user_states[sender_id]["data"].get("username", "")
        password = user_states[sender_id]["data"].get("password", "")
        
        try:
            # Gọi API crawl thực tế
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.crawl_url,
                    json={
                        "username": username,
                        "password": password,
                        "state": True
                    }
                )
                
                if response.status_code == 200:
                    crawl_result = response.json()
                    
                    # Sau khi crawl xong, chuyển sang trạng thái chat
                    user_states[sender_id]["state"] = UserState.CHATTING
                    
                    responses = []
                    responses.append(self._create_text_message(
                        sender_id, 
                        f"Đăng nhập thành công! {crawl_result.get('message', '')}"
                    ))
                    responses.extend(self._redirect_to_chat(sender_id))
                    
                    return responses
                else:
                    # Nếu có lỗi, vẫn chuyển sang trạng thái chat
                    user_states[sender_id]["state"] = UserState.CHATTING
                    
                    return [
                        self._create_text_message(
                            sender_id, 
                            f"Đăng nhập không thành công: {response.text}. Nhưng bạn vẫn có thể tiếp tục chat."
                        )
                    ] + self._redirect_to_chat(sender_id)
        except Exception as e:
            # Nếu có lỗi, vẫn chuyển sang trạng thái chat
            user_states[sender_id]["state"] = UserState.CHATTING
            
            return [
                self._create_text_message(
                    sender_id, 
                    f"Đã xảy ra lỗi: {str(e)}. Nhưng bạn vẫn có thể tiếp tục chat."
                )
            ] + self._redirect_to_chat(sender_id)
    
    def _redirect_to_chat(self, sender_id: str) -> List[Dict[str, Any]]:
        """
        Chuyển hướng người dùng sang API chat
        """
        return [
            self._create_text_message(
                sender_id, 
                "Bạn đã được chuyển sang hệ thống chat. Bạn có thể đặt câu hỏi ngay bây giờ."
            )
        ]
    
    async def _call_chat_api(self, sender_id: str, query: str) -> List[Dict[str, Any]]:
        """
        Gọi API chat với câu hỏi của người dùng
        """
        try:
            # Gọi API chat thực tế
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.chat_url,
                    json={"query": query}
                )
                
                if response.status_code == 200:
                    chat_result = response.json()
                    answer = chat_result.get("answer", "Không có câu trả lời.")
                    
                    return [self._create_text_message(sender_id, answer)]
                else:
                    return [self._create_text_message(sender_id, f"Lỗi khi gọi API chat: {response.text}")]
        except Exception as e:
            return [self._create_text_message(sender_id, f"Đã xảy ra lỗi: {str(e)}")]
    
    def _create_text_message(self, recipient_id: str, text: str) -> Dict[str, Any]:
        """
        Tạo tin nhắn văn bản
        """
        return {
            "recipient": {"id": recipient_id},
            "message": {"text": text}
        }
    
    def send_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gửi tin nhắn đến Facebook
        """
        params = {"access_token": self.page_access_token}
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(
            self.api_url,
            params=params,
            headers=headers,
            data=json.dumps(message_data)
        )
        
        return response.json()

# Khởi tạo singleton instance
facebook_service = FacebookService() 