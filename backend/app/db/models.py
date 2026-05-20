from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)

    portfolios: Mapped[list["Portfolio"]] = relationship(back_populates="user")
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user")
    feature_usage: Mapped[list["FeatureUsage"]] = relationship(back_populates="user")
    watchlist_items: Mapped[list["WatchlistItem"]] = relationship(back_populates="user")
    broker_connections: Mapped[list["BrokerConnection"]] = relationship(back_populates="user")


class Portfolio(TimestampMixin, Base):
    __tablename__ = "portfolios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    base_currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    benchmark_symbol: Mapped[str | None] = mapped_column(String(24), nullable=True)
    risk_free_rate: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)

    user: Mapped[User] = relationship(back_populates="portfolios")
    holdings: Mapped[list["Holding"]] = relationship(back_populates="portfolio")
    snapshots: Mapped[list["PortfolioSnapshot"]] = relationship(back_populates="portfolio")
    analytics_results: Mapped[list["AnalyticsResult"]] = relationship(back_populates="portfolio")
    ai_conversations: Mapped[list["AIConversation"]] = relationship(back_populates="portfolio")
    upload_jobs: Mapped[list["UploadJob"]] = relationship(back_populates="portfolio")
    watchlist_items: Mapped[list["WatchlistItem"]] = relationship(back_populates="portfolio")
    broker_accounts: Mapped[list["BrokerAccount"]] = relationship(back_populates="portfolio")


class Asset(TimestampMixin, Base):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    symbol: Mapped[str] = mapped_column(String(24), unique=True, index=True, nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    sector: Mapped[str | None] = mapped_column(String(120), nullable=True)
    asset_class: Mapped[str | None] = mapped_column(String(80), nullable=True)
    exchange: Mapped[str | None] = mapped_column(String(80), nullable=True)

    prices: Mapped[list["AssetPrice"]] = relationship(back_populates="asset")


class Holding(TimestampMixin, Base):
    __tablename__ = "holdings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"), index=True, nullable=False)
    symbol: Mapped[str] = mapped_column(String(24), index=True, nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    quantity: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    average_cost: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    current_price: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    sector: Mapped[str | None] = mapped_column(String(120), nullable=True)
    asset_class: Mapped[str | None] = mapped_column(String(80), nullable=True)
    exchange: Mapped[str | None] = mapped_column(String(80), nullable=True)

    portfolio: Mapped[Portfolio] = relationship(back_populates="holdings")


class AssetPrice(TimestampMixin, Base):
    __tablename__ = "asset_prices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    asset_id: Mapped[str | None] = mapped_column(ForeignKey("assets.id"), nullable=True)
    symbol: Mapped[str] = mapped_column(String(24), index=True, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    source: Mapped[str] = mapped_column(String(80), nullable=False)
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_realtime: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    asset: Mapped[Asset | None] = relationship(back_populates="prices")


class PortfolioSnapshot(TimestampMixin, Base):
    __tablename__ = "portfolio_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"), index=True, nullable=False)
    total_value: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    cash_value: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    holdings_value: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    snapshot_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    portfolio: Mapped[Portfolio] = relationship(back_populates="snapshots")


class AnalyticsResult(TimestampMixin, Base):
    __tablename__ = "analytics_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"), index=True, nullable=False)
    result_type: Mapped[str] = mapped_column(String(80), nullable=False)
    result_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    portfolio: Mapped[Portfolio] = relationship(back_populates="analytics_results")


class AIConversation(TimestampMixin, Base):
    __tablename__ = "ai_conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"), index=True, nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    context_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)

    portfolio: Mapped[Portfolio] = relationship(back_populates="ai_conversations")
    messages: Mapped[list["AIMessage"]] = relationship(back_populates="conversation")


class AIMessage(TimestampMixin, Base):
    __tablename__ = "ai_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("ai_conversations.id"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(40), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)

    conversation: Mapped[AIConversation] = relationship(back_populates="messages")


class UploadJob(TimestampMixin, Base):
    __tablename__ = "upload_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"), index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    total_rows: Mapped[int] = mapped_column(default=0, nullable=False)
    valid_rows: Mapped[int] = mapped_column(default=0, nullable=False)
    invalid_rows: Mapped[int] = mapped_column(default=0, nullable=False)
    column_mapping_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)

    portfolio: Mapped[Portfolio] = relationship(back_populates="upload_jobs")
    rows: Mapped[list["UploadRow"]] = relationship(back_populates="upload_job")


class UploadRow(TimestampMixin, Base):
    __tablename__ = "upload_rows"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    upload_job_id: Mapped[str] = mapped_column(ForeignKey("upload_jobs.id"), index=True, nullable=False)
    row_number: Mapped[int] = mapped_column(nullable=False)
    raw_data_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    mapped_data_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    validation_errors_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)

    upload_job: Mapped[UploadJob] = relationship(back_populates="rows")


class Subscription(TimestampMixin, Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    plan_tier: Mapped[str] = mapped_column(String(40), default="free", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False)
    provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    provider_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped[User] = relationship(back_populates="subscriptions")


class FeatureUsage(TimestampMixin, Base):
    __tablename__ = "feature_usage"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    feature: Mapped[str] = mapped_column(String(80), nullable=False)
    usage_count: Mapped[int] = mapped_column(default=0, nullable=False)
    period: Mapped[str] = mapped_column(String(40), nullable=False)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)

    user: Mapped[User] = relationship(back_populates="feature_usage")


class WatchlistItem(TimestampMixin, Base):
    __tablename__ = "watchlist_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    portfolio_id: Mapped[str | None] = mapped_column(ForeignKey("portfolios.id"), nullable=True)
    symbol: Mapped[str] = mapped_column(String(24), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship(back_populates="watchlist_items")
    portfolio: Mapped[Portfolio | None] = relationship(back_populates="watchlist_items")


class BrokerConnection(TimestampMixin, Base):
    __tablename__ = "broker_connections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    external_connection_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)

    user: Mapped[User] = relationship(back_populates="broker_connections")
    accounts: Mapped[list["BrokerAccount"]] = relationship(back_populates="broker_connection")


class BrokerAccount(TimestampMixin, Base):
    __tablename__ = "broker_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    broker_connection_id: Mapped[str] = mapped_column(
        ForeignKey("broker_connections.id"), index=True, nullable=False
    )
    portfolio_id: Mapped[str | None] = mapped_column(ForeignKey("portfolios.id"), nullable=True)
    account_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    account_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    external_account_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)

    broker_connection: Mapped[BrokerConnection] = relationship(back_populates="accounts")
    portfolio: Mapped[Portfolio | None] = relationship(back_populates="broker_accounts")


Index("ix_upload_rows_job_row_number", UploadRow.upload_job_id, UploadRow.row_number)
