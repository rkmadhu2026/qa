from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.core.database import get_db
from app.core.deps import AuthContext, get_current_ctx
from app.schemas.merchant import (BranchCreate, BranchOut,
                                  TerminalCreate, TerminalOut)

router = APIRouter(prefix="/api/v1", tags=["merchants"])


# ---- Branches ----
@router.get("/branches", response_model=list[BranchOut])
def list_branches(db: Session = Depends(get_db),
                  ctx: AuthContext = Depends(get_current_ctx)):
    return db.scalars(
        select(models.Branch).where(models.Branch.tenant_id == ctx.tenant_id)
    ).all()


@router.post("/branches", response_model=BranchOut)
def create_branch(body: BranchCreate, db: Session = Depends(get_db),
                  ctx: AuthContext = Depends(get_current_ctx)):
    b = models.Branch(tenant_id=ctx.tenant_id, **body.model_dump())
    db.add(b); db.commit(); db.refresh(b)
    return b


# ---- Terminals ----
@router.get("/terminals", response_model=list[TerminalOut])
def list_terminals(db: Session = Depends(get_db),
                   ctx: AuthContext = Depends(get_current_ctx)):
    return db.scalars(
        select(models.Terminal).where(models.Terminal.tenant_id == ctx.tenant_id)
    ).all()


@router.post("/terminals", response_model=TerminalOut)
def create_terminal(body: TerminalCreate, db: Session = Depends(get_db),
                    ctx: AuthContext = Depends(get_current_ctx)):
    branch = db.get(models.Branch, body.branch_id)
    if not branch or branch.tenant_id != ctx.tenant_id:
        raise HTTPException(404, "Branch not found")
    t = models.Terminal(tenant_id=ctx.tenant_id, **body.model_dump())
    db.add(t); db.commit(); db.refresh(t)
    return t
