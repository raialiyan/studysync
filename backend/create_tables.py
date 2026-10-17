from database import Base, engine
from models import (
    User,
    Workspace,
    Membership,
    Module,
    Task,
    Comment,
)

Base.metadata.create_all(bind=engine)

print("All StudySync database tables created!")