from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, field_validator

from app.models import PlanType, ScheduleFrequency, ScheduleStatus, PaymentMethod, PaymentStatus


# ---------- Auth ----------

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    phone_number: str
    password: str
    confirm_password: str
    agree_to_terms: bool

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v

    @field_validator("agree_to_terms")
    @classmethod
    def must_agree(cls, v):
        if not v:
            raise ValueError("You must agree to the Terms & Conditions")
        return v


class UserLogin(BaseModel):
    identifier: str  # username OR phone number
    password: str
    remember_me: bool = False


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    phone_number: str
    plan: PlanType
    messages_used_this_month: int
    whatsapp_connected: bool

    class Config:
        from_attributes = True


# ---------- WhatsApp ----------

class WhatsAppGroupOut(BaseModel):
    id: int
    group_name: str
    member_count: int

    class Config:
        from_attributes = True


class WhatsAppConnectRequest(BaseModel):
    whatsapp_number: str


# ---------- Schedules ----------

class ScheduleCreate(BaseModel):
    target_group_id: Optional[int] = None
    target_group_name: str
    message_body: str
    frequency: ScheduleFrequency = ScheduleFrequency.once
    scheduled_date: str  # "YYYY-MM-DD"
    scheduled_time: str  # "HH:MM"


class ScheduleUpdate(BaseModel):
    message_body: Optional[str] = None
    frequency: Optional[ScheduleFrequency] = None
    scheduled_date: Optional[str] = None
    scheduled_time: Optional[str] = None
    status: Optional[ScheduleStatus] = None


class ScheduleOut(BaseModel):
    id: int
    target_group_name: str
    message_body: str
    frequency: ScheduleFrequency
    scheduled_date: str
    scheduled_time: str
    status: ScheduleStatus
    times_sent: int
    created_at: datetime

    class Config:
        from_attributes = True


class HomeSummary(BaseModel):
    username: str
    plan: PlanType
    messages_used_this_month: int
    message_limit: int
    active_schedules: int
    sent_messages: int
    upcoming: List[ScheduleOut]


# ---------- Subscription ----------

class PlanOut(BaseModel):
    id: str
    name: str
    price_lkr: float
    message_limit: int
    badge: Optional[str] = None


class PayHereInitRequest(BaseModel):
    plan: PlanType


class PayHereInitResponse(BaseModel):
    merchant_id: str
    order_id: str
    amount: str
    currency: str = "LKR"
    hash: str
    return_url: str
    cancel_url: str
    notify_url: str
    checkout_action_url: str


class BankTransferOut(BaseModel):
    bank_name: str
    account_name: str
    account_number: str
    branch: str


class PaymentTransactionOut(BaseModel):
    id: int
    plan: PlanType
    amount_lkr: float
    method: PaymentMethod
    status: PaymentStatus
    created_at: datetime

    class Config:
        from_attributes = True
