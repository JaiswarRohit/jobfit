import html
from typing import List, Tuple, Optional
import httpx
from app.schemas.job import JobMatchResult
from app.config import settings


class TelegramService:
    BASE_URL = "https://api.telegram.org/bot{token}/{method}"

    @classmethod
    def _get_credentials(cls, bot_token: str = None, chat_id: str = None) -> Tuple[str, str]:
        token = bot_token or settings.TELEGRAM_BOT_TOKEN or ""
        chat = chat_id or settings.TELEGRAM_CHAT_ID or ""

        token = str(token).strip().strip("'\"")
        chat = str(chat).strip().strip("'\"")

        # Strip full URL if user pasted https://api.telegram.org/bot<token>
        if "api.telegram.org/bot" in token:
            token = token.split("api.telegram.org/bot")[-1].split("/")[0]

        # Strip accidental "bot" prefix (e.g. user pasted 'bot123456:ABC...')
        if token.lower().startswith("bot") and ":" in token:
            token = token[3:]

        if not token or not chat:
            raise ValueError(
                "Telegram Bot Token or Chat ID is missing. "
                "Provide them in the request or set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env"
            )
        return token.strip(), chat.strip()

    @classmethod
    async def test_connection(cls, bot_token: str, chat_id: str) -> Tuple[bool, str]:
        """Test sending a ping message to verify token and chat ID."""
        try:
            token, chat = cls._get_credentials(bot_token, chat_id)
            url = cls.BASE_URL.format(token=token, method="sendMessage")
            payload = {
                "chat_id": chat,
                "text": "🤖 <b>JobFit AI Connected Successfully!</b>\n\nYou will receive your top matching LinkedIn jobs right here.",
                "parse_mode": "HTML"
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload)
                data = res.json()
                if res.status_code == 200 and data.get("ok"):
                    print("✅ [Telegram] Connection verified! Test ping delivered successfully.")
                    return True, "Telegram connection verified! Test message sent to your chat."
                else:
                    err = data.get("description", "Unknown Telegram API error")
                    hint = ""
                    if "chat not found" in err.lower():
                        if chat.startswith("@"):
                            hint = " (Telegram bots cannot message personal @usernames directly. Please use your numeric Chat ID from @userinfobot)."
                        else:
                            hint = " (Have you opened your bot in Telegram and clicked START / sent /start? You must start the bot first)."
                    elif "unauthorized" in err.lower():
                        hint = " (Please verify your Bot Token from @BotFather)."
                    elif "blocked" in err.lower():
                        hint = " (The bot is blocked by the user. Please unblock it in Telegram)."

                    full_err = f"Telegram API error: {err}{hint}"
                    print(f"❌ [Telegram Test Failed] {full_err}")
                    return False, full_err
        except Exception as e:
            err_msg = f"Failed to connect to Telegram: {str(e)}"
            print(f"❌ [Telegram Test Exception] {err_msg}")
            return False, err_msg

    @classmethod
    def format_job_message(cls, match: JobMatchResult, rank: int = 1) -> str:
        """Format a single matched job post into a clean, rich HTML Telegram message."""
        job = match.job
        
        # Emoji indicator based on match rate
        if match.match_percentage >= 80:
            badge = "🔥 <b>TOP MATCH (High Selection Likelihood)</b>"
        elif match.match_percentage >= 65:
            badge = "⭐ <b>STRONG MATCH</b>"
        else:
            badge = "📌 <b>POTENTIAL MATCH</b>"

        safe_title = html.escape(job.title)
        safe_company = html.escape(job.company)
        safe_location = html.escape(job.location)
        safe_summary = html.escape(match.match_summary)
        safe_url = job.url

        matching_str = ", ".join(match.matching_skills[:5]) if match.matching_skills else "Core tech stack"
        missing_str = ", ".join(match.missing_skills[:4]) if match.missing_skills else "None"

        message = (
            f"{badge}\n\n"
            f"🎯 <b>#{rank} {safe_title}</b>\n"
            f"🏢 <b>Company:</b> {safe_company}\n"
            f"📍 <b>Location:</b> {safe_location}\n"
            f"📅 <b>Posted:</b> {job.posted_date}\n"
            f"💼 <b>Experience Level:</b> {job.experience_level or 'Mid-Senior'}\n\n"
            f"📊 <b>Profile Match:</b> <code>{match.match_percentage}%</code>\n"
            f"🏆 <b>Selection Likelihood:</b> <b>{match.selection_probability}</b>\n\n"
            f"✅ <b>Matching Skills:</b>\n<i>{matching_str}</i>\n\n"
            f"⚠️ <b>Missing / Desired Skills:</b>\n<i>{missing_str}</i>\n\n"
            f"💡 <b>Recruiter Insight:</b>\n{safe_summary}\n\n"
            f"🔗 <a href=\"{safe_url}\"><b>View & Apply on LinkedIn</b></a>"
        )
        return message

    @classmethod
    async def send_matching_jobs(
        cls,
        jobs: List[JobMatchResult],
        bot_token: str = None,
        chat_id: str = None,
        top_n: Optional[int] = None
    ) -> Tuple[int, List[str]]:
        """Send all matched jobs (or top N if specified) to Telegram."""
        import asyncio
        token, chat = cls._get_credentials(bot_token, chat_id)
        
        # If top_n is specified and > 0, take slice; otherwise deliver ALL matched jobs
        if top_n and top_n > 0:
            selected_jobs = jobs[:top_n]
        else:
            selected_jobs = jobs

        sent_count = 0
        errors: List[str] = []

        if not selected_jobs:
            return 0, ["No matching jobs available to send."]

        # 1. Send Header Alert
        header_text = (
            f"🚀 <b>JobFit AI Scan Complete</b>\n\n"
            f"Found <b>{len(selected_jobs)}</b> matching jobs on LinkedIn for your profile.\n"
            f"Auto-dispatching <b>ALL {len(selected_jobs)}</b> jobs directly to this Telegram chat!\n"
            f"Top match rating: <b>{selected_jobs[0].match_percentage}%</b>."
        )
        url = cls.BASE_URL.format(token=token, method="sendMessage")

        async with httpx.AsyncClient(timeout=12.0) as client:
            try:
                res = await client.post(url, json={
                    "chat_id": chat,
                    "text": header_text,
                    "parse_mode": "HTML"
                })
                data = res.json()
                if res.status_code != 200 or not data.get("ok"):
                    err_desc = data.get("description", "Unknown error")
                    errors.append(f"Header alert send error: {err_desc}")
                    print(f"❌ [Telegram Send] Header alert failed: {err_desc}")
            except Exception as e:
                errors.append(f"Header send error: {str(e)}")
                print(f"❌ [Telegram Send] Header exception: {e}")

            # 2. Send each job card with safe spacing to prevent Telegram 429 rate limit
            for idx, match in enumerate(selected_jobs, start=1):
                try:
                    card_text = cls.format_job_message(match, rank=idx)
                    res = await client.post(url, json={
                        "chat_id": chat,
                        "text": card_text,
                        "parse_mode": "HTML",
                        "disable_web_page_preview": False
                    })
                    data = res.json()
                    if res.status_code == 200 and data.get("ok"):
                        sent_count += 1
                    else:
                        err_desc = data.get("description", "Unknown error")
                        errors.append(f"Job #{idx} send error: {err_desc}")
                        print(f"❌ [Telegram Send] Job #{idx} failed: {err_desc}")
                except Exception as e:
                    errors.append(f"Job #{idx} exception: {str(e)}")
                    print(f"❌ [Telegram Send] Job #{idx} exception: {e}")

                # Rate-limiting delay between messages to avoid Telegram flood limits
                if idx < len(selected_jobs):
                    await asyncio.sleep(0.35)

        return sent_count, errors
