from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    tenant_name: str
    tenant_code: str
    email: EmailStr
    password: str
    full_name: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant_id: str
    user_id: str
    email: EmailStr
    roles: list[str]
