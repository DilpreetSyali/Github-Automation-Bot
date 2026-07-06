import asyncio
import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, Header, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.gemini_client import triage_issue
from app.github_client import add_label, post_comment
from app.models import ActionLog, Event, Repo, Rule
from app.slack_client import send_slack_message

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger("webhooks")

MAX_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = [1, 3]  # delay before attempt 2, attempt 3


def _verify_signature(raw_body: bytes, signature_header: str | None) -> bool:
    """Constant-time HMAC-SHA256 check against GITHUB_WEBHOOK_SECRET.
    This is what stops forged requests from third parties hitting this
    endpoint and being treated as real GitHub events."""
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256
    ).hexdigest()
    provided = signature_header.split("=", 1)[1]
    return hmac.compare_digest(expected, provided)


async def _retry(coro_factory, action_type: str, event: Event, db: Session):
    """Runs an outbound call (GitHub write-back / Slack notify) with retries.
    Every attempt — success or failure — is written to ActionLog, so a
    downstream outage shows up as visible failed attempts rather than a
    silently dropped event."""
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            result = await coro_factory()
            db.add(ActionLog(
                event_id=event.id,
                action_type=action_type,
                status="success",
                detail=str(result)[:1000],
                attempt=attempt,
            ))
            db.commit()
            return
        except Exception as exc:  # noqa: BLE001 - we want to log and retry any failure
            last_error = exc
            db.add(ActionLog(
                event_id=event.id,
                action_type=action_type,
                status="failed",
                detail=str(exc)[:1000],
                attempt=attempt,
            ))
            db.commit()
            if attempt < MAX_ATTEMPTS:
                await asyncio.sleep(RETRY_BACKOFF_SECONDS[attempt - 1])
    logger.error("Action %s exhausted retries for event %s: %s", action_type, event.id, last_error)


def _extract_matchable(event_type: str, payload: dict) -> tuple[dict, int | None]:
    """Pulls the fields rules can match against, plus the issue/PR number
    GitHub write-back APIs need."""
    obj = payload.get("issue") or payload.get("pull_request") or {}
    fields = {
        "title": obj.get("title", ""),
        "body": obj.get("body") or "",
        "author": (obj.get("user") or {}).get("login", ""),
    }
    number = obj.get("number") or payload.get("number")
    return fields, number


def _rule_matches(rule: Rule, fields: dict) -> bool:
    value = (fields.get(rule.match_field) or "").lower()
    target = (rule.match_value or "").lower()
    if rule.match_type == "equals":
        return value == target
    return target in value


@router.post("/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
    x_github_delivery: str | None = Header(default=None),
):
    raw_body = await request.body()

    if not _verify_signature(raw_body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")

    if not x_github_delivery or not x_github_event:
        raise HTTPException(status_code=400, detail="Missing GitHub headers")

    payload = json.loads(raw_body)
    repo_info = payload.get("repository") or {}
    owner = (repo_info.get("owner") or {}).get("login")
    name = repo_info.get("name")
    action = payload.get("action")

    db = SessionLocal()
    try:
        repo = db.query(Repo).filter(Repo.owner == owner, Repo.name == name).first()
        if not repo:
            # Not a repo we manage (or not connected yet) - accept but don't record,
            # so GitHub doesn't retry a webhook we intentionally ignore.
            logger.warning("Webhook for unknown repo %s/%s", owner, name)
            return {"ok": True, "recorded": False}

        event = Event(
            repo_id=repo.id,
            delivery_id=x_github_delivery,
            event_type=x_github_event,
            action=action,
            payload=raw_body.decode("utf-8", errors="replace"),
            status="received",
        )
        db.add(event)
        try:
            db.commit()
        except IntegrityError:
            # Same delivery ID already processed (GitHub redelivery after a
            # timeout on our end, or a genuine replay). Idempotent no-op.
            db.rollback()
            logger.info("Duplicate delivery %s ignored", x_github_delivery)
            return {"ok": True, "duplicate": True}
        db.refresh(event)

        await _process_event(db, repo, event, payload)
        return {"ok": True}
    finally:
        db.close()


async def _process_event(db: Session, repo: Repo, event: Event, payload: dict) -> None:
    try:
        fields, issue_number = _extract_matchable(event.event_type, payload)
        access_token = repo.owner_user.access_token

        # --- AI TRIAGE (issues only, on open/reopen) ---
        ai_result = None
        if (
            event.event_type == "issues"
            and event.action in ("opened", "reopened")
            and issue_number
            and settings.GEMINI_API_KEY
        ):
            ai_result = await triage_issue(fields["title"], fields["body"])
            if ai_result:
                # Apply AI-suggested label
                await _retry(
                    lambda label=ai_result["label"]: add_label(
                        access_token, repo.owner, repo.name, issue_number, label
                    ),
                    "ai_label", event, db,
                )
                # Post AI summary as a comment on the issue
                comment = (
                    f"🤖 **AI Triage**\n\n"
                    f"**Suggested label:** `{ai_result['label']}`\n"
                    f"**Summary:** {ai_result['summary']}"
                )
                await _retry(
                    lambda c=comment: post_comment(
                        access_token, repo.owner, repo.name, issue_number, c
                    ),
                    "ai_comment", event, db,
                )
                # Send enriched Slack message
                slack_text = (
                    f":robot_face: *AI Triage* — *{repo.owner}/{repo.name}*\n"
                    f"*Issue:* \"{fields['title']}\"\n"
                    f"*Label:* `{ai_result['label']}`\n"
                    f"*Summary:* {ai_result['summary']}"
                )
                await _retry(lambda t=slack_text: send_slack_message(t), "ai_slack", event, db)

        # --- RULE-BASED PROCESSING ---
        rules = (
            db.query(Rule)
            .filter(Rule.repo_id == repo.id, Rule.event_type == event.event_type, Rule.enabled == True)  # noqa: E712
            .all()
        )

        matched_any = False
        for rule in rules:
            if not _rule_matches(rule, fields):
                continue
            matched_any = True

            if rule.add_label and issue_number:
                await _retry(
                    lambda: add_label(access_token, repo.owner, repo.name, issue_number, rule.add_label),
                    "github_label", event, db,
                )
            if rule.post_comment and issue_number:
                await _retry(
                    lambda: post_comment(access_token, repo.owner, repo.name, issue_number, rule.post_comment),
                    "github_comment", event, db,
                )
            if rule.slack_notify:
                ai_note = f"\n🤖 _{ai_result['summary']}_" if ai_result else ""
                text = (
                    f":robot_face: *{repo.owner}/{repo.name}* — {event.event_type} "
                    f"{event.action or ''}: \"{fields['title']}\" matched rule *{rule.name}*{ai_note}"
                )
                await _retry(lambda: send_slack_message(text), "slack_notify", event, db)

        event.status = "processed"
        _ = matched_any
    except Exception as exc:  # noqa: BLE001
        event.status = "failed"
        event.error = str(exc)[:2000]
        logger.exception("Failed processing event %s", event.id)
    finally:
        import datetime as dt
        event.processed_at = dt.datetime.utcnow()
        db.commit()
