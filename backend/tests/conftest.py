import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, engine


@pytest.fixture(autouse=True)
def ensure_db_tables():
    """Đảm bảo các bảng CSDL được tạo đầy đủ trước khi chạy test."""
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db_session():
    """Tạo isolated in-memory SQLite database session cho từng unit test."""
    test_engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)
