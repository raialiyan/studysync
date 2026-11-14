"""StudySync integration test fixtures. NEVER connect to the development database."""
import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# conftest is loaded from backend/tests; run pytest from backend/
from database import Base, get_db
import models  # noqa: F401; register all original tables
import week3_api  # noqa: F401; register activities
from main import app


def guarded_test_url():
    raw = os.getenv("STUDYSYNC_TEST_DATABASE_URL")
    if not raw:
        pytest.exit("Set STUDYSYNC_TEST_DATABASE_URL to a dedicated local PostgreSQL database named studysync_test (see README).", returncode=2)
    url = make_url(raw)
    if (url.get_backend_name() != "postgresql"
            or url.database != "studysync_test"
            or url.host not in ("localhost", "127.0.0.1", None)):
        pytest.exit("REFUSING: test database must be local PostgreSQL named exactly studysync_test.", returncode=2)
    return raw


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(guarded_test_url())
    # All tables in dedicated test DB will be cleared by individual tests.
    yield engine
    engine.dispose()


@pytest.fixture
def client(test_engine):
    # Isolated database; each test starts from a freshly created schema.
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    Factory = sessionmaker(bind=test_engine, expire_on_commit=False)

    def override_db():
        with Factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=test_engine)
