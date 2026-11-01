from fastapi import APIRouter, HTTPException
from app.schemas.telegram import (
    TelegramConfigRequest,
    TelegramTestResponse,
    TelegramSendJobsRequest,
    TelegramSendResponse
)
from app.services.telegram_service import TelegramService
from app.services.db_service import DBService
from app.config import settings

router = APIRouter(prefix="/api/telegram", tags=["Telegram Bot Notifier"])


@router.post("/test", response_model=TelegramTestResponse)
async def test_telegram_bot(config: TelegramConfigRequest):
    """
    Test your Telegram Bot Token and Chat ID by sending a confirmation ping.
    If valid, automatically persists them to SQLite and .env.
    """
    success, message = await TelegramService.test_connection(
        bot_token=config.bot_token,
        chat_id=config.chat_id
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)

    # Automatically save verified credentials to SQLite and .env
    token = config.bot_token.strip()
    chat = config.chat_id.strip()
    DBService.save_user_profile({
        "telegram_bot_token": token,
        "telegram_chat_id": chat
    }, user_id=1)
    settings.TELEGRAM_BOT_TOKEN = token
    settings.TELEGRAM_CHAT_ID = chat

    return TelegramTestResponse(success=True, message=f"{message} (Credentials saved to database)")


@router.post("/save")
async def save_telegram_credentials(config: TelegramConfigRequest):
    """
    Save Telegram Bot Token and Chat ID to SQLite database and .env configuration.
    """
    if not config.bot_token or not config.chat_id:
        raise HTTPException(status_code=400, detail="Both Telegram Bot Token and Chat ID are required.")

    token = config.bot_token.strip()
    chat = config.chat_id.strip()

    DBService.save_user_profile({
        "telegram_bot_token": token,
        "telegram_chat_id": chat
    }, user_id=1)

    settings.TELEGRAM_BOT_TOKEN = token
    settings.TELEGRAM_CHAT_ID = chat

    return {
        "success": True,
        "message": "Telegram Bot Token and Chat ID saved successfully to SQLite database and .env!"
    }


@router.post("/send", response_model=TelegramSendResponse)
async def send_jobs_to_telegram(request: TelegramSendJobsRequest):
    """
    Send top-matching jobs with percentage scores, selection likelihood,
    and LinkedIn links directly to Telegram.
    """
    if not request.jobs:
        raise HTTPException(status_code=400, detail="No matched jobs provided to send.")

    try:
        sent_count, errors = await TelegramService.send_matching_jobs(
            jobs=request.jobs,
            bot_token=request.bot_token,
            chat_id=request.chat_id,
            top_n=request.top_n
        )

        return TelegramSendResponse(
            success=sent_count > 0,
            sent_count=sent_count,
            message=f"Successfully sent {sent_count} jobs to Telegram bot!",
            errors=errors
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to dispatch to Telegram: {str(e)}")
