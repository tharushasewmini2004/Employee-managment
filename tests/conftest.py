# tests/conftest.py
"""Shared test setup: a fresh, empty in-memory database for every test."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401  (loads the models so the tables are known)
from app.database import Base, get_db
from app.main import app


@pytest.fixture
def session_factory():
    """Create a brand-new SQLite database in memory, with all tables, for one test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    yield factory
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(session_factory):
    """A database session for unit tests of the service layer."""
    session = session_factory()
    yield session
    session.close()


@pytest.fixture
def client(session_factory):
    """An API client whose requests use the test database instead of PostgreSQL."""

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    