from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class AuthContext:
    def __init__(self, user_id: UUID, tenant_id: UUID, email: str, roles: list[str]):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.email = email
        self.roles = roles


def get_current_ctx(token: str = Depends(oauth2_scheme)) -> AuthContext:
    try:
        payload = decode_access_token(token)
    except ValueError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(e))
    return AuthContext(
        user_id=UUID(payload["sub"]),
        tenant_id=UUID(payload["tid"]),
        email=payload["email"],
        roles=payload.get("roles", []),
    )


def require_roles(*allowed: str):
    def _check(ctx: AuthContext = Depends(get_current_ctx)) -> AuthContext:
        if allowed and not set(allowed) & set(ctx.roles):
            raise HTTPException(status.HTTP_403_FORBIDDEN,
                                f"Requires role in {allowed}")
        return ctx
    return _check


# Convenience: a DB session scoped to the caller's tenant.
def get_tenant_db(ctx: AuthContext = Depends(get_current_ctx),
                  db: Session = Depends(get_db)):
    # Ensures every route sees db + tenant context together.
    return db, ctx
