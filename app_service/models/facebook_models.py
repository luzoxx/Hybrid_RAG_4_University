from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class FacebookVerification(BaseModel):
    hub_mode: str
    hub_verify_token: str
    hub_challenge: str

class FacebookMessage(BaseModel):
    mid: str
    text: str

class FacebookQuickReply(BaseModel):
    payload: str
    title: Optional[str] = None

class FacebookPostback(BaseModel):
    payload: str
    title: Optional[str] = None

class FacebookSender(BaseModel):
    id: str

class FacebookRecipient(BaseModel):
    id: str

class FacebookMessaging(BaseModel):
    sender: FacebookSender
    recipient: FacebookRecipient
    timestamp: int
    message: Optional[FacebookMessage] = None
    postback: Optional[FacebookPostback] = None

class FacebookEntry(BaseModel):
    id: str
    time: int
    messaging: List[FacebookMessaging]

class FacebookWebhookEvent(BaseModel):
    object: str
    entry: List[FacebookEntry]
    
class FacebookResponse(BaseModel):
    recipient: Dict[str, str]
    message: Dict[str, Any] 