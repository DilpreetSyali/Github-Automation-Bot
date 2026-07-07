import httpx

from app.config import settings

SLACK_API = "https://slack.com/api"


async def exchange_code_for_slack_token(code: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{SLACK_API}/oauth.v2.access",
            params={
                "client_id": settings.SLACK_CLIENT_ID,
                "client_secret": settings.SLACK_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.SLACK_OAUTH_REDIRECT_URL,
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise ValueError(data)
        return data


async def list_channels(access_token: str) -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{SLACK_API}/conversations.list",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"types": "public_channel,private_channel", "limit": 200},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise ValueError(data)
        return data.get("channels", [])


async def join_channel(access_token: str, channel_id: str) -> None:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{SLACK_API}/conversations.join",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json; charset=utf-8"},
            json={"channel": channel_id},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(str(data))


async def send_slack_message(text: str, access_token: str | None = None, channel_id: str | None = None, webhook_url: str | None = None) -> None:
    if webhook_url:
        async with httpx.AsyncClient() as client:
            resp = await client.post(webhook_url, json={"text": text}, timeout=10)
            resp.raise_for_status()
            return

    if not access_token or not channel_id:
        raise RuntimeError("Slack connection is not configured")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{SLACK_API}/chat.postMessage",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json; charset=utf-8"},
            json={"channel": channel_id, "text": text},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(str(data))
