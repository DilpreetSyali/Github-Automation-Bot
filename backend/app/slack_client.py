import httpx

from app.config import settings


async def send_slack_message(text: str) -> None:
    if not settings.SLACK_WEBHOOK_URL:
        raise RuntimeError("SLACK_WEBHOOK_URL is not configured")
    async with httpx.AsyncClient() as client:
        resp = await client.post(settings.SLACK_WEBHOOK_URL, json={"text": text}, timeout=10)
        resp.raise_for_status()
