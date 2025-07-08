from pydantic import BaseModel
from typing import Optional, Dict, Any

class CrawlRequest(BaseModel):
    username: str
    password: str
    state: bool = True

class CrawlResponse(BaseModel):
    status: str
    message: str
    next_endpoint: str
    data: Optional[Dict[str, Any]] = None 