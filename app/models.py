import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, Enum
)
from sqlalchemy.orm import relationship

from app.database import Base


class PlanType(str, enum.Enum):
    free = "free"
    pro_500 = "pro_500"
    unlimited = "unlimited"


class ScheduleFrequency(str, enum.Enum):
    once = "once"
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


class ScheduleStatus(str, enum.Enum):
    active = "active"
    paused = "paused"


class PaymentMethod(str, enum.Enum):
    payhere = "payhere"
    bank_transfer = "bank_transfer"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    rejected = "rejected"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    phone_number = Column(String(20), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    agreed_to_terms = Column(Boolean, default=False, nullable=False)

    plan = Column(Enum(PlanType), default=PlanType.free, nullable=False)
    messages_used_this_month = Column(Integer, default=0, nullable=False)
    subscription_expires_at = Column(DateTime, nullable=True)

    whatsapp_connected = Column(Boolean, default=False, nullable=False)
    whatsapp_number = Column(String(20), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    schedules = relationship("ScheduleReminder", back_populates="owner", cascade="all, delete-orphan")
    whatsapp_groups = relationship("WhatsAppGroup", back_populates="owner", cascade="all, delete-orphan")
    payments = relationship("PaymentTransaction", back_populates="user", cascade="all, delete-orphan")

    def message_limit(self, settings) -> int:
        if self.plan == PlanType.free:
            return settings.FREE_PLAN_MESSAGE_LIMIT
        if self.plan == PlanType.pro_500:
            return settings.PRO_PLAN_MESSAGE_LIMIT
        return -1  # unlimited


class WhatsAppGroup(Base):
    __tablename__ = "whatsapp_groups"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    external_group_id = Column(String(100), nullable=False)
    group_name = Column(String(150), nullable=False)
    member_count = Column(Integer, default=0)

    owner = relationship("User", back_populates="whatsapp_groups")


class ScheduleReminder(Base):
    __tablename__ = "schedule_reminders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    target_group_id = Column(Integer, ForeignKey("whatsapp_groups.id"), nullable=True)
    target_group_name = Column(String(150), nullable=False)

    message_body = Column(Text, nullable=False)
    frequency = Column(Enum(ScheduleFrequency), default=ScheduleFrequency.once, nullable=False)
    scheduled_date = Column(String(20), nullable=False)   # "YYYY-MM-DD"
    scheduled_time = Column(String(10), nullable=False)   # "HH:MM"
    status = Column(Enum(ScheduleStatus), default=ScheduleStatus.active, nullable=False)

    times_sent = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="schedules")
    logs = relationship("MessageLog", back_populates="schedule", cascade="all, delete-orphan")


class MessageLog(Base):
    __tablename__ = "message_logs"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedule_reminders.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="sent")
    content = Column(Text, nullable=False)

    schedule = relationship("ScheduleReminder", back_populates="logs")


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan = Column(Enum(PlanType), nullable=False)
    amount_lkr = Column(Float, nullable=False)
    method = Column(Enum(PaymentMethod), nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.pending, nullable=False)
    payhere_order_id = Column(String(100), nullable=True)
    receipt_image_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="payments")
