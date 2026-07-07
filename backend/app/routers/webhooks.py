import asyncio
import datetime as dt
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
from app.github_client import add_label, create_label, post_comment
from app.models import ActionLog, Event, Repo, Rule, SlackConnection
from app.slack_client import send_slack_message

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger("webhooks")

MAX_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = [1, 3]


def _verify_signature(raw_body: bytes, signature_header: str | None) -> bool:
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256
    ).hexdigest()
    provided = signature_header.split("=", 1)[1]
    return hmac.compare_digest(expected, provided)


async def _retry(coro_factory, action_type: str, event: Event, db: Session):
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            result = await coro_factory()
            db.add(
                ActionLog(
                    event_id=event.id,
                    action_type=action_type,
                    status="success",
                    detail=str(result)[:1000],
                    attempt=attempt,
                )
            )
            db.commit()
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            db.add(
                ActionLog(
                    event_id=event.id,
                    action_type=action_type,
                    status="failed",
                    detail=str(exc)[:1000],
                    attempt=attempt,
                )
            )
            db.commit()
            if attempt < MAX_ATTEMPTS:
                await asyncio.sleep(RETRY_BACKOFF_SECONDS[attempt - 1])
    logger.error("Action %s exhausted retries for event %s: %s", action_type, event.id, last_error)


def _extract_matchable(event_type: str, payload: dict) -> tuple[dict, int | None]:
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
        slack_conn = db.query(SlackConnection).filter(SlackConnection.user_id == repo.user_id).first()
        slack_access_token = slack_conn.access_token if slack_conn else None
        slack_channel_id = slack_conn.channel_id if slack_conn else None
        slack_webhook = slack_conn.webhook_url if slack_conn else None

        ai_result = None
        if event.event_type in ("issues", "pull_request") and event.action in ("opened", "reopened", "closed") and issue_number:
            ai_result = await triage_issue(fields["title"], fields["body"])
            if ai_result:
                issue_is_urgent = bool(ai_result.get("urgent"))
                await _ensure_label(access_token, repo.owner, repo.name, ai_result["label"])
                await _retry(
                    lambda label=ai_result["label"]: add_label(
                        access_token, repo.owner, repo.name, issue_number, label
                    ),
                    "ai_label",
                    event,
                    db,
                )
                comment = (
                    "🤖 **AI Triage**\n\n"
                    f"**Suggested label:** `{ai_result['label']}`\n"
                    f"**Summary:** {ai_result['summary']}"
                )
                await _retry(
                    lambda c=comment: post_comment(
                        access_token, repo.owner, repo.name, issue_number, c
                    ),
                    "ai_comment",
                    event,
                    db,
                )

                urgent = event.action == "opened" and (
                    issue_is_urgent or ai_result["label"] == "bug"
                )
                slack_text = _build_slack_message(
                    repo.owner,
                    repo.name,
                    event.action or "updated",
                    event.event_type,
                    fields["title"],
                    ai_result["label"],
                    ai_result["summary"],
                    urgent=urgent,
                )
                await _retry(
                    lambda t=slack_text: send_slack_message(t, slack_access_token, slack_channel_id, slack_webhook),
                    "ai_slack",
                    event,
                    db,
                )
            else:
                urgent = event.action == "opened"
                slack_text = _build_slack_message(
                    repo.owner,
                    repo.name,
                    event.action or "updated",
                    event.event_type,
                    fields["title"],
                    "untriaged",
                    "AI triage unavailable",
                    urgent=urgent,
                )
                await _retry(
                    lambda t=slack_text: send_slack_message(t, slack_access_token, slack_channel_id, slack_webhook),
                    "ai_slack",
                    event,
                    db,
                )

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
                await _ensure_label(access_token, repo.owner, repo.name, rule.add_label)
                await _retry(
                    lambda: add_label(access_token, repo.owner, repo.name, issue_number, rule.add_label),
                    "github_label",
                    event,
                    db,
                )
            if rule.post_comment and issue_number:
                await _retry(
                    lambda: post_comment(access_token, repo.owner, repo.name, issue_number, rule.post_comment),
                    "github_comment",
                    event,
                    db,
                )
            if rule.slack_notify:
                ai_note = f"\n🤖 _{ai_result['summary']}_" if ai_result else ""
                text = (
                    f":robot_face: *{repo.owner}/{repo.name}* — {event.event_type} "
                    f"{event.action or ''}: \"{fields['title']}\" matched rule *{rule.name}*{ai_note}"
                )
                await _retry(
                    lambda: send_slack_message(text, slack_access_token, slack_channel_id, slack_webhook),
                    "slack_notify",
                    event,
                    db,
                )

        event.status = "processed"
        _ = matched_any
    except Exception as exc:  # noqa: BLE001
        event.status = "failed"
        event.error = str(exc)[:2000]
        logger.exception("Failed processing event %s", event.id)
    finally:
        event.processed_at = dt.datetime.utcnow()
        db.commit()


async def _ensure_label(access_token: str, owner: str, repo: str, label: str) -> None:
    await create_label(access_token, owner, repo, label)


def _build_slack_message(
    owner: str,
    repo: str,
    action: str,
    event_type: str,
    title: str,
    label: str,
    summary: str,
    urgent: bool = False,
) -> str:
    prefix = ":rotating_light: " if urgent else ":speech_balloon: "
    item_name = "PR" if event_type == "pull_request" else "Issue"
    heading = f"URGENT {item_name}" if urgent else f"{item_name} update"
    return (
        f"{prefix}*{heading}* — *{owner}/{repo}*\n"
        f"*Action:* {action}\n"
        f"*{item_name}:* \"{title}\"\n"
        f"*Label:* `{label}`\n"
        f"*Summary:* {summary}"
    )
