import pytest
from app.core.database import Base, engine


@pytest.fixture(autouse=True)
def ensure_db_tables():
    """Đảm bảo các bảng CSDL được tạo đầy đủ trước khi chạy test."""
    Base.metadata.create_all(bind=engine)
    yield
