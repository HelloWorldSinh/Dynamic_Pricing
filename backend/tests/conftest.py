import os
from pathlib import Path

# Ưu tiên sử dụng dynamic_pricing.db có sẵn để test kiểm tra dữ liệu thật, tránh phụ thuộc PostgreSQL server
DEFAULT_DB_FILE = Path(__file__).resolve().parent.parent / "dynamic_pricing.db"
if DEFAULT_DB_FILE.exists():
    os.environ["DATABASE_URL"] = f"sqlite:///{DEFAULT_DB_FILE.as_posix()}"
else:
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base, engine


@pytest.fixture(autouse=True)
def ensure_db_tables():
    """Đảm bảo các bảng CSDL được tạo đầy đủ trước khi chạy test nếu engine kết nối được."""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        # Khi chạy trong môi trường CI/Sandbox không có PostgreSQL local, bỏ qua để db_session SQLite in-memory tự tạo
        pass
    yield


@pytest.fixture
def db_session():
    """Tạo isolated in-memory SQLite database session cho từng unit test."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)
