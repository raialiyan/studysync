
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class WorkspaceUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class WorkspaceResponse(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class MemberAdd(BaseModel):
    email: EmailStr


class MemberResponse(BaseModel):
    user_id: int
    email: EmailStr
    role: str


class ModuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class ModuleUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class ModuleResponse(BaseModel):
    id: int
    name: str
    workspace_id: int
    model_config = ConfigDict(from_attributes=True)
