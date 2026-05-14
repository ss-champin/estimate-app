import uuid
from datetime import date, datetime
from enum import Enum as PyEnum
from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class PlanEnum(str, PyEnum):
    free = "free"
    paid = "paid"


class SubscriptionStatusEnum(str, PyEnum):
    active   = "active"
    canceled = "canceled"
    past_due = "past_due"


class BillingPlan(Base):
    """料金プラン（利用上限・Stripe Price ID・見積もりAI用プランキー）。課金・レート制限の参照元。"""

    __tablename__ = "billing_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    slug: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    stripe_price_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    daily_request_limit: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    monthly_request_limit: Mapped[int] = mapped_column(Integer(), nullable=False)
    estimate_plan_key: Mapped[str] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text("true"))
    sort_order: Mapped[int] = mapped_column(Integer(), nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"
    id:         Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    clerk_id:   Mapped[str]       = mapped_column(String(255), nullable=False, unique=True)
    email:      Mapped[str]       = mapped_column(String(255), nullable=False, unique=True)
    plan:       Mapped[str]       = mapped_column(Enum(PlanEnum, name="plan_enum"), nullable=False, server_default="free")
    created_at: Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())

    subscription: Mapped["Subscription | None"] = relationship("Subscription", back_populates="user", uselist=False)
    api_usages:   Mapped[list["ApiUsage"]]       = relationship("ApiUsage", back_populates="user")

    @property
    def is_paid(self) -> bool:
        return self.plan == PlanEnum.paid.value


class Subscription(Base):
    __tablename__ = "subscriptions"
    id:                     Mapped[uuid.UUID]       = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id:                Mapped[uuid.UUID]       = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    stripe_customer_id:     Mapped[str | None]      = mapped_column(String(255))
    stripe_subscription_id: Mapped[str | None]      = mapped_column(String(255))
    status:                 Mapped[str]             = mapped_column(Enum(SubscriptionStatusEnum, name="subscription_status_enum"), nullable=False, server_default="active")
    current_period_end:     Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at:             Mapped[datetime]        = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:             Mapped[datetime]        = mapped_column(DateTime(timezone=True), server_default=func.now())
    user: Mapped[User] = relationship("User", back_populates="subscription")


class ApiUsage(Base):
    __tablename__ = "api_usage"
    id:         Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id:    Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    usage_date: Mapped[date]      = mapped_column(Date(), nullable=False)
    count:      Mapped[int]       = mapped_column(Integer(), nullable=False, server_default="0")
    __table_args__ = (UniqueConstraint("user_id", "usage_date", name="uq_api_usage_user_date"),)
    user: Mapped[User] = relationship("User", back_populates="api_usages")
