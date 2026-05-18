"""initial models

Revision ID: 0001_initial_models
Revises:
Create Date: 2026-05-18
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_models"
down_revision = None
branch_labels = None
depends_on = None


def timestamp_columns() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=True),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "assets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("symbol", sa.String(length=24), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("sector", sa.String(length=120), nullable=True),
        sa.Column("asset_class", sa.String(length=80), nullable=True),
        sa.Column("exchange", sa.String(length=80), nullable=True),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol"),
    )
    op.create_index("ix_assets_symbol", "assets", ["symbol"])

    op.create_table(
        "portfolios",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("base_currency", sa.String(length=3), nullable=False),
        sa.Column("benchmark_symbol", sa.String(length=24), nullable=True),
        sa.Column("risk_free_rate", sa.Numeric(10, 6), nullable=True),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_portfolios_user_id", "portfolios", ["user_id"])

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("plan_tier", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=True),
        sa.Column("provider_subscription_id", sa.String(length=255), nullable=True),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])

    op.create_table(
        "feature_usage",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("feature", sa.String(length=80), nullable=False),
        sa.Column("usage_count", sa.Integer(), nullable=False),
        sa.Column("period", sa.String(length=40), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_feature_usage_user_id", "feature_usage", ["user_id"])

    op.create_table(
        "broker_connections",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("external_connection_id", sa.String(length=255), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_broker_connections_user_id", "broker_connections", ["user_id"])

    op.create_table(
        "holdings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("portfolio_id", sa.String(length=36), nullable=False),
        sa.Column("symbol", sa.String(length=24), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("average_cost", sa.Numeric(18, 6), nullable=True),
        sa.Column("current_price", sa.Numeric(18, 6), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("sector", sa.String(length=120), nullable=True),
        sa.Column("asset_class", sa.String(length=80), nullable=True),
        sa.Column("exchange", sa.String(length=80), nullable=True),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_holdings_portfolio_id", "holdings", ["portfolio_id"])
    op.create_index("ix_holdings_symbol", "holdings", ["symbol"])

    op.create_table(
        "asset_prices",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("asset_id", sa.String(length=36), nullable=True),
        sa.Column("symbol", sa.String(length=24), nullable=False),
        sa.Column("price", sa.Numeric(18, 6), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_realtime", sa.Boolean(), nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_asset_prices_symbol", "asset_prices", ["symbol"])

    op.create_table(
        "portfolio_snapshots",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("portfolio_id", sa.String(length=36), nullable=False),
        sa.Column("total_value", sa.Numeric(18, 6), nullable=True),
        sa.Column("cash_value", sa.Numeric(18, 6), nullable=True),
        sa.Column("holdings_value", sa.Numeric(18, 6), nullable=True),
        sa.Column("snapshot_json", sa.Text(), nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_portfolio_snapshots_portfolio_id", "portfolio_snapshots", ["portfolio_id"])

    op.create_table(
        "analytics_results",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("portfolio_id", sa.String(length=36), nullable=False),
        sa.Column("result_type", sa.String(length=80), nullable=False),
        sa.Column("result_json", sa.Text(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analytics_results_portfolio_id", "analytics_results", ["portfolio_id"])

    op.create_table(
        "ai_conversations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("portfolio_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("context_json", sa.Text(), nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_conversations_portfolio_id", "ai_conversations", ["portfolio_id"])

    op.create_table(
        "upload_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("portfolio_id", sa.String(length=36), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=False),
        sa.Column("valid_rows", sa.Integer(), nullable=False),
        sa.Column("invalid_rows", sa.Integer(), nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_upload_jobs_portfolio_id", "upload_jobs", ["portfolio_id"])

    op.create_table(
        "watchlist_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("portfolio_id", sa.String(length=36), nullable=True),
        sa.Column("symbol", sa.String(length=24), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_watchlist_items_user_id", "watchlist_items", ["user_id"])

    op.create_table(
        "broker_accounts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("broker_connection_id", sa.String(length=36), nullable=False),
        sa.Column("portfolio_id", sa.String(length=36), nullable=True),
        sa.Column("account_name", sa.String(length=120), nullable=True),
        sa.Column("account_type", sa.String(length=80), nullable=True),
        sa.Column("external_account_id", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["broker_connection_id"], ["broker_connections.id"]),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_broker_accounts_broker_connection_id", "broker_accounts", ["broker_connection_id"])

    op.create_table(
        "ai_messages",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("conversation_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=40), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=True),
        sa.Column("model", sa.String(length=120), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["conversation_id"], ["ai_conversations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_messages_conversation_id", "ai_messages", ["conversation_id"])

    op.create_table(
        "upload_rows",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("upload_job_id", sa.String(length=36), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("raw_data_json", sa.Text(), nullable=False),
        sa.Column("mapped_data_json", sa.Text(), nullable=False),
        sa.Column("validation_errors_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["upload_job_id"], ["upload_jobs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_upload_rows_upload_job_id", "upload_rows", ["upload_job_id"])
    op.create_index("ix_upload_rows_job_row_number", "upload_rows", ["upload_job_id", "row_number"])


def downgrade() -> None:
    op.drop_table("upload_rows")
    op.drop_table("ai_messages")
    op.drop_table("broker_accounts")
    op.drop_table("watchlist_items")
    op.drop_table("upload_jobs")
    op.drop_table("ai_conversations")
    op.drop_table("analytics_results")
    op.drop_table("portfolio_snapshots")
    op.drop_table("asset_prices")
    op.drop_table("holdings")
    op.drop_table("broker_connections")
    op.drop_table("feature_usage")
    op.drop_table("subscriptions")
    op.drop_table("portfolios")
    op.drop_table("assets")
    op.drop_table("users")
