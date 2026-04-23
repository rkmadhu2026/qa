import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.core.database import get_db
from app.core.security import (create_access_token, hash_password,
                               verify_password)
from app.schemas.auth import LoginResponse, SignupRequest

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/signup", response_model=LoginResponse)
def signup(body: SignupRequest, db: Session = Depends(get_db)):
    """Create tenant + first admin user. For MVP. In prod, split these."""
    if db.scalar(select(models.Tenant).where(models.Tenant.code == body.tenant_code)):
        raise HTTPException(400, "tenant_code already exists")

    tenant = models.Tenant(name=body.tenant_name, code=body.tenant_code)
    db.add(tenant)
    db.flush()

    user = models.User(
        tenant_id=tenant.id,
        email=body.email,
        full_name=body.full_name,
        password_hash=hash_password(body.password),
        roles=["admin", "cashier"],
    )
    db.add(user)
    db.commit()

    token = create_access_token(user_id=user.id, tenant_id=tenant.id,
                                email=user.email, roles=user.roles)
    return LoginResponse(access_token=token, tenant_id=str(tenant.id),
                         user_id=str(user.id), email=user.email,
                         roles=user.roles)


@router.post("/login", response_model=LoginResponse)
def login(form: OAuth2PasswordRequestForm = Depends(),
          db: Session = Depends(get_db)):
    # Username = email (OAuth2 form compatibility)
    user = db.scalar(select(models.User).where(models.User.email == form.username))
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    token = create_access_token(user_id=user.id, tenant_id=user.tenant_id,
                                email=user.email, roles=user.roles)
    return LoginResponse(access_token=token, tenant_id=str(user.tenant_id),
                         user_id=str(user.id), email=user.email, roles=user.roles)
