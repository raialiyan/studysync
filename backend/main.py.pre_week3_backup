
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

from database import get_db
from models import User, Workspace, Membership, Module
from schemas import (
    UserCreate, UserResponse, UserLogin, TokenResponse,
    WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse,
    MemberAdd, MemberResponse,
    ModuleCreate, ModuleUpdate, ModuleResponse
)
from security import hash_password, verify_password
from auth import create_access_token, get_current_user

app = FastAPI(title="StudySync API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"]
)



@app.get("/health")
def health():
    return {"status": "ok"}


# -------------------------------
# AUTHENTICATION
# -------------------------------

@app.post("/register", response_model=UserResponse, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    email = str(data.email).lower()

    existing = db.scalar(
        select(User).where(User.email == email)
    )

    if existing:
        raise HTTPException(400, "Email already registered")

    user = User(
        email=email,
        hashed_password=hash_password(data.password)
    )

    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Email already registered")

    db.refresh(user)
    return user


@app.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.scalar(
        select(User).where(
            User.email == str(data.email).lower()
        )
    )

    if user is None or not verify_password(
        data.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return {
        "access_token": create_access_token(user.id),
        "token_type": "bearer"
    }


@app.get("/users/me", response_model=UserResponse)
def users_me(user: User = Depends(get_current_user)):
    return user


# -------------------------------
# WORKSPACE SECURITY HELPERS
# -------------------------------

def get_membership(db, workspace_id, user_id):
    workspace = db.get(Workspace, workspace_id)

    if workspace is None:
        raise HTTPException(404, "Workspace not found")

    membership = db.scalar(
        select(Membership).where(
            Membership.workspace_id == workspace_id,
            Membership.user_id == user_id
        )
    )

    if membership is None:
        raise HTTPException(404, "Workspace not found")

    return membership


def require_owner(db, workspace_id, user_id):
    membership = get_membership(
        db, workspace_id, user_id
    )

    if membership.role != "owner":
        raise HTTPException(403, "Owner permission required")

    return membership


def get_module_for_member(db, module_id, user_id):
    module = db.get(Module, module_id)

    if module is None:
        raise HTTPException(404, "Module not found")

    get_membership(db, module.workspace_id, user_id)
    return module


# -------------------------------
# WORKSPACE CRUD
# -------------------------------

@app.post(
    "/workspaces",
    response_model=WorkspaceResponse,
    status_code=201
)
def create_workspace(
    data: WorkspaceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    workspace = Workspace(name=data.name.strip())
    if not workspace.name:
        raise HTTPException(422, "Workspace name cannot be blank")

    db.add(workspace)
    db.flush()

    membership = Membership(
        user_id=user.id,
        workspace_id=workspace.id,
        role="owner"
    )

    db.add(membership)
    db.commit()
    db.refresh(workspace)

    return workspace


@app.get("/workspaces", response_model=list[WorkspaceResponse])
def list_workspaces(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return db.scalars(
        select(Workspace)
        .join(Membership)
        .where(Membership.user_id == user.id)
        .order_by(Workspace.id)
    ).all()


@app.get(
    "/workspaces/{workspace_id}",
    response_model=WorkspaceResponse
)
def read_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    get_membership(db, workspace_id, user.id)
    return db.get(Workspace, workspace_id)


@app.patch(
    "/workspaces/{workspace_id}",
    response_model=WorkspaceResponse
)
def update_workspace(
    workspace_id: int,
    data: WorkspaceUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    require_owner(db, workspace_id, user.id)

    workspace = db.get(Workspace, workspace_id)
    name = data.name.strip()

    if not name:
        raise HTTPException(422, "Workspace name cannot be blank")

    workspace.name = name
    db.commit()
    db.refresh(workspace)

    return workspace


@app.delete("/workspaces/{workspace_id}", status_code=204)
def delete_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    require_owner(db, workspace_id, user.id)

    workspace = db.get(Workspace, workspace_id)
    db.delete(workspace)
    db.commit()


# -------------------------------
# WORKSPACE MEMBERSHIPS
# -------------------------------

@app.get(
    "/workspaces/{workspace_id}/members",
    response_model=list[MemberResponse]
)
def list_members(
    workspace_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    get_membership(db, workspace_id, user.id)

    rows = db.execute(
        select(Membership, User)
        .join(User, Membership.user_id == User.id)
        .where(Membership.workspace_id == workspace_id)
    ).all()

    return [
        MemberResponse(
            user_id=member.user_id,
            email=member_user.email,
            role=member.role
        )
        for member, member_user in rows
    ]


@app.post(
    "/workspaces/{workspace_id}/members",
    response_model=MemberResponse,
    status_code=201
)
def add_member(
    workspace_id: int,
    data: MemberAdd,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    require_owner(db, workspace_id, user.id)

    target = db.scalar(
        select(User).where(
            User.email == str(data.email).lower()
        )
    )

    if target is None:
        raise HTTPException(404, "User not found")

    existing = db.scalar(
        select(Membership).where(
            Membership.workspace_id == workspace_id,
            Membership.user_id == target.id
        )
    )

    if existing:
        raise HTTPException(409, "Already a member")

    member = Membership(
        workspace_id=workspace_id,
        user_id=target.id,
        role="member"
    )

    db.add(member)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Already a member")

    return MemberResponse(
        user_id=target.id,
        email=target.email,
        role="member"
    )


@app.delete(
    "/workspaces/{workspace_id}/members/{member_user_id}",
    status_code=204
)
def remove_member(
    workspace_id: int,
    member_user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    require_owner(db, workspace_id, user.id)

    member = db.scalar(
        select(Membership).where(
            Membership.workspace_id == workspace_id,
            Membership.user_id == member_user_id
        )
    )

    if member is None:
        raise HTTPException(404, "Member not found")

    if member.role == "owner":
        raise HTTPException(403, "Cannot remove an owner")

    db.delete(member)
    db.commit()


@app.delete(
    "/workspaces/{workspace_id}/leave",
    status_code=204
)
def leave_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    member = get_membership(db, workspace_id, user.id)

    if member.role == "owner":
        raise HTTPException(
            403,
            "Owner must delete or transfer the workspace"
        )

    db.delete(member)
    db.commit()


# -------------------------------
# MODULE CRUD
# -------------------------------

@app.post(
    "/workspaces/{workspace_id}/modules",
    response_model=ModuleResponse,
    status_code=201
)
def create_module(
    workspace_id: int,
    data: ModuleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    get_membership(db, workspace_id, user.id)

    name = data.name.strip()
    if not name:
        raise HTTPException(422, "Module name cannot be blank")

    module = Module(
        workspace_id=workspace_id,
        name=name
    )

    db.add(module)
    db.commit()
    db.refresh(module)

    return module


@app.get(
    "/workspaces/{workspace_id}/modules",
    response_model=list[ModuleResponse]
)
def list_modules(
    workspace_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    get_membership(db, workspace_id, user.id)

    return db.scalars(
        select(Module)
        .where(Module.workspace_id == workspace_id)
        .order_by(Module.id)
    ).all()


@app.patch(
    "/modules/{module_id}",
    response_model=ModuleResponse
)
def update_module(
    module_id: int,
    data: ModuleUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    module = get_module_for_member(db, module_id, user.id)

    name = data.name.strip()
    if not name:
        raise HTTPException(422, "Module name cannot be blank")

    module.name = name
    db.commit()
    db.refresh(module)

    return module


@app.delete("/modules/{module_id}", status_code=204)
def delete_module(
    module_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    module = get_module_for_member(db, module_id, user.id)

    db.delete(module)
    db.commit()
