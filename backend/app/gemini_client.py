"""Gemini AI triage.

Given an issue title + body, returns a suggested label, urgency signal, and a
one-sentence summary. Falls back gracefully if the API key is missing or the
call fails.
"""

import logging

import httpx

from app.config import settings

logger = logging.getLogger("gemini")

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash-lite:generateContent"
)

VALID_LABELS = [
    "bug",
    "enhancement",
    "question",
    "documentation",
    "help wanted",
    "invalid",
    "wontfix",
]

URGENCY_KEYWORDS = [
    "urgent",
    "critical",
    "prod",
    "production down",
    "down",
    "failing",
    "failure",
    "outage",
    "broken",
    "sev1",
    "severe",
]

LABEL_KEYWORDS = {
    "bug": ["bug", "broken", "error", "fail", "failure", "crash", "not working", "down"],
    "question": ["how do i", "how to", "can i", "what is", "why does", "help"],
    "documentation": ["docs", "documentation", "readme", "typo", "spell"],
    "help wanted": ["help wanted", "needs help", "good first issue"],
    "wontfix": ["wontfix", "won't fix", "not going to fix"],
    "invalid": ["invalid", "spam", "test"],
    "enhancement": [],
}

SYSTEM_PROMPT = """You are a GitHub issue triage assistant. Given an issue title and body, respond with exactly three lines:
Line 1: A label from this list only: bug, enhancement, question, documentation, help wanted, invalid, wontfix
Line 2: urgent or normal
Line 3: A one-sentence summary of what the issue is about (max 20 words).

Do not include any other text, explanation, or formatting. Just three lines."""


async def triage_issue(title: str, body: str) -> dict | None:
    """Returns {"label": str, "urgent": bool, "summary": str} or None."""
    fallback = _fallback_triage(title, body)
    if not settings.GEMINI_API_KEY:
        return fallback

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
            if len(lines) < 3:
                return None
            label = lines[0].lower().strip()
            urgency = lines[1].lower().strip()
            summary = lines[2].strip()
            if label not in VALID_LABELS:
                # try to find a valid label in the response
                for valid in VALID_LABELS:
                    if valid in label:
                        label = valid
                        break
                else:
                    label = "enhancement"
            urgent = urgency.startswith("urgent")
            return {"label": label, "urgent": urgent, "summary": summary}
    except Exception as exc:
        logger.warning("Gemini triage failed: %s", exc)
        return fallback


def _fallback_triage(title: str, body: str) -> dict:
    text = f"{title}\n{body or ''}".lower()
    urgent = any(keyword in text for keyword in URGENCY_KEYWORDS)

    label = "enhancement"
    for candidate, keywords in LABEL_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            label = candidate
            break

    summary = title.strip() or "Issue reported without a title"
    if len(summary.split()) > 20:
        summary = " ".join(summary.split()[:20])

    return {"label": label, "urgent": urgent, "summary": summary}
