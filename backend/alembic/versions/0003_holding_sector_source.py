"""add holding sector source metadata

Revision ID: 0003_holding_sector_source
Revises: 0002_upload_column_mapping
Create Date: 2026-05-21
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_holding_sector_source"
down_revision = "0002_upload_column_mapping"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("holdings") as batch_op:
        batch_op.add_column(sa.Column("sector_source", sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column("sector_updated_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("holdings") as batch_op:
        batch_op.drop_column("sector_updated_at")
        batch_op.drop_column("sector_source")
