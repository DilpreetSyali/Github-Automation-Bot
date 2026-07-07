from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Repo, Rule, User
from app.schemas import RuleIn, RuleOut

router = APIRouter(prefix="/repos/{repo_id}/rules", tags=["rules"])


def _get_owned_repo(repo_id: int, user: User, db: Session) -> Repo:
    repo = db.query(Repo).filter(Repo.id == repo_id, Repo.user_id == user.id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")
    return repo


@router.get("", response_model=list[RuleOut])
async def list_rules(repo_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = _get_owned_repo(repo_id, user, db)
    return db.query(Rule).filter(Rule.repo_id == repo.id).all()


@router.post("", response_model=RuleOut)
async def create_rule(
    repo_id: int,
    body: RuleIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = _get_owned_repo(repo_id, user, db)
    data = body.dict()
    if not data.get("name"):
        label = data.get("add_label") or "automation"
        data["name"] = f"{data['event_type']} → {label}"
    rule = Rule(repo_id=repo.id, **data)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.put("/{rule_id}", response_model=RuleOut)
async def update_rule(
    repo_id: int,
    rule_id: int,
    body: RuleIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = _get_owned_repo(repo_id, user, db)
    rule = db.query(Rule).filter(Rule.id == rule_id, Rule.repo_id == repo.id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    data = body.dict()
    if not data.get("name"):
        label = data.get("add_label") or "automation"
        data["name"] = f"{data['event_type']} → {label}"
    for k, v in data.items():
        setattr(rule, k, v)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}")
async def delete_rule(
    repo_id: int,
    rule_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = _get_owned_repo(repo_id, user, db)
    rule = db.query(Rule).filter(Rule.id == rule_id, Rule.repo_id == repo.id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()
    return {"ok": True}
