"""Tiện ích xử lý múi giờ chuẩn Việt Nam (UTC+7 / GMT+7).

Cung cấp các hàm tạo thời gian nhất quán cho toàn bộ hệ thống:
- Lưu vào cơ sở dữ liệu (SQLite/PostgreSQL) dưới dạng naive datetime khớp chuẩn giờ Việt Nam.
- Sinh chuỗi ISO 8601 kèm múi giờ (+07:00) cho API responses và RAM task progress tracking.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

# Múi giờ chuẩn Việt Nam (UTC+7)
VIETNAM_TZ = timezone(timedelta(hours=7))


def get_vietnam_now() -> datetime:
    """Lấy thời điểm hiện tại theo múi giờ Việt Nam (UTC+7).

    Trả về naive datetime (tzinfo=None) mang đúng ngày/giờ/phút/giây của Việt Nam
    để tương thích chuẩn với kiểu cột DateTime của SQLAlchemy trên SQLite và PostgreSQL,
    đảm bảo khi truy vấn trực tiếp CSDL sẽ thấy đúng mốc thời gian Việt Nam.
    """
    return datetime.now(VIETNAM_TZ).replace(tzinfo=None)


def get_vietnam_now_aware() -> datetime:
    """Lấy thời điểm hiện tại theo múi giờ Việt Nam (UTC+7) có thông tin timezone (+07:00)."""
    return datetime.now(VIETNAM_TZ)


def to_vietnam_iso(dt: Optional[datetime] = None) -> str:
    """Chuyển đổi đối tượng datetime sang chuỗi chuẩn ISO 8601 kèm múi giờ Việt Nam (+07:00).

    - Nếu dt là None: Lấy thời gian hiện tại theo giờ Việt Nam.
    - Nếu dt là naive datetime: Giả định là giờ Việt Nam và gán tzinfo=VIETNAM_TZ.
    - Nếu dt là timezone-aware: Chuyển đổi (astimezone) sang múi giờ Việt Nam.
    """
    if dt is None:
        return datetime.now(VIETNAM_TZ).isoformat()
    if dt.tzinfo is None:
        return dt.replace(tzinfo=VIETNAM_TZ).isoformat()
    return dt.astimezone(VIETNAM_TZ).isoformat()
