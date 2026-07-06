"""Gemini AI triage — given an issue title + body, returns a suggested label
and a one-sentence summary. Falls back gracefully if the API key is missing
or the call fails."""

import logging

import httpx

from app.config import settings

logger = logging.getLogger("gemini")

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent"
)

VALID_LABELS = ["bug", "enhancement", "question", "documentation", "help wanted", "invalid", "wontfix"]

SYSTEM_PROMPT = """You are a GitHub issue triage assistant. Given an issue title and body, respond with exactly two lines:
Line 1: A label from this list only: bug, enhancement, question, documentation, help wanted, invalid, wontfix
Line 2: A one-sentence summary of what the issue is about (max 20 words).

Do not include any other text, explanation, or formatting. Just two lines."""


async def triage_issue(title: str, body: str) -> dict | None:
    """Returns {"label": str, "summary": str} or None if triage fails."""
    if not settings.GEMINI_API_KEY:
        return None

    prompt = f"Title: {title}\n\nBody: {body or '(no description provided)'}"

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                GEMINI_URL,
                params={"key": settings.GEMINI_API_KEY},
                json={
                    "contents": [
                        {"parts": [{"text": SYSTEM_PROMPT + "\n\n" + prompt}]}
                    ],
                    "generationConfig": {
                        "temperature": 0.1,
                        "maxOutputTokens": 100,
                    },
                },
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
            if len(lines) < 2:
                return None
            label = lines[0].lower().strip()
            summary = lines[1].strip()
            if label not in VALID_LABELS:
                # try to find a valid label in the response
                for valid in VALID_LABELS:
                    if valid in label:
                        label = valid
                        break
                else:
                    label = "enhancement"
            return {"label": label, "summary": summary}
    except Exception as exc:
        logger.warning("Gemini triage failed: %s", exc)
        return None
