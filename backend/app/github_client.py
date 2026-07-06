import httpx

from app.config import settings

GITHUB_API = "https://api.github.com"


async def exchange_code_for_token(code: str) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GITHUB_OAUTH_REDIRECT_URL,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        if "access_token" not in data:
            raise ValueError(f"GitHub OAuth exchange failed: {data}")
        return data["access_token"]


async def get_authenticated_user(access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GITHUB_API}/user",
            headers=_auth_headers(access_token),
        )
        resp.raise_for_status()
        return resp.json()


async def list_user_repos(access_token: str) -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GITHUB_API}/user/repos",
            headers=_auth_headers(access_token),
            params={"per_page": 100, "sort": "updated"},
        )
        resp.raise_for_status()
        return resp.json()


async def create_webhook(access_token: str, owner: str, repo: str, webhook_url: str, secret: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{GITHUB_API}/repos/{owner}/{repo}/hooks",
            headers=_auth_headers(access_token),
            json={
                "name": "web",
                "active": True,
                "events": ["issues", "pull_request", "push"],
                "config": {
                    "url": webhook_url,
                    "content_type": "json",
                    "secret": secret,
                    "insecure_ssl": "0",
                },
            },
        )
        resp.raise_for_status()
        return resp.json()


async def add_label(access_token: str, owner: str, repo: str, issue_number: int, label: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{GITHUB_API}/repos/{owner}/{repo}/issues/{issue_number}/labels",
            headers=_auth_headers(access_token),
            json={"labels": [label]},
        )
        resp.raise_for_status()
        return resp.json()


async def post_comment(access_token: str, owner: str, repo: str, issue_number: int, body: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{GITHUB_API}/repos/{owner}/{repo}/issues/{issue_number}/comments",
            headers=_auth_headers(access_token),
            json={"body": body},
        )
        resp.raise_for_status()
        return resp.json()


def _auth_headers(access_token: str) -> dict:
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
