from fastapi import FastAPI, status
from pydantic import BaseModel, Field

app = FastAPI()

# Temporary in-memory storage
workspaces = []


# Define the expected request body
class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1)


@app.get("/")
def home():
    return {"message": "Welcome to StudySync API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/workspaces", status_code=status.HTTP_201_CREATED)
def create_workspace(workspace: WorkspaceCreate):

    new_workspace = {
        "id": len(workspaces) + 1,
        "name": workspace.name
    }

    workspaces.append(new_workspace)

    return new_workspace


@app.get("/workspaces")
def get_workspaces():
    return workspaces