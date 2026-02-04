from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from datetime import datetime, timezone, timedelta
from database import Base

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    plan_type = Column(String, default="trial")
    trial_start = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    trial_end = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc) + timedelta(days=7)
    )

    is_trial_active = Column(Boolean, default=True)