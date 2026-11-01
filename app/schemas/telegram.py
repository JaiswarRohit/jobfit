from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.job import JobMatchResult


class TelegramConfigRequest(BaseModel):
    bot_token: str = Field(..., description="Telegram Bot Token from @BotFather")
    chat_id: str = Field(..., description="Telegram Chat ID or channel ID")


class TelegramTestResponse(BaseModel):
    success: bool
    message: str


class TelegramSendJobsRequest(BaseModel):
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None
    jobs: List[JobMatchResult]
    top_n: Optional[int] = Field(default=None, description="Send top N matching jobs, or None / 0 to send ALL matching jobs without limit")


class TelegramSendResponse(BaseModel):
    success: bool
    sent_count: int
    message: str
    errors: List[str] = []
