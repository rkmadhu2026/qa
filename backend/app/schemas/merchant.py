from uuid import UUID
from pydantic import BaseModel


class BranchCreate(BaseModel):
    name: str
    code: str
    phone: str | None = None


class BranchOut(BaseModel):
    id: UUID
    name: str
    code: str
    status: str

    class Config:
        from_attributes = True


class TerminalCreate(BaseModel):
    name: str
    code: str
    branch_id: UUID
    device_type: str | None = None


class TerminalOut(BaseModel):
    id: UUID
    name: str
    code: str
    branch_id: UUID
    status: str

    class Config:
        from_attributes = True
