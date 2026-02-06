from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from database import Base
from datetime import datetime, timezone

class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    endpoint = Column(String)  # e.g., "/sheets", "/users"
    method = Column(String)    # e.g., "GET" or "POST"
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))