"""Skill 管理（骨架）。"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Skill

router = APIRouter()


class ToggleIn(BaseModel):
    enabled: bool


@router.get("")
def list_skills(db: Session = Depends(get_db)):
    rows = db.query(Skill).all()
    return [
        {"id": s.id, "name": s.name, "version": s.version, "enabled": s.enabled}
        for s in rows
    ]


@router.post("/{skill_id}/enable")
def toggle_skill(skill_id: str, body: ToggleIn, db: Session = Depends(get_db)):
    skill = db.get(Skill, skill_id)
    if not skill:
        raise HTTPException(404, "skill not found")
    skill.enabled = body.enabled
    db.commit()
    return {"ok": True, "enabled": skill.enabled}
