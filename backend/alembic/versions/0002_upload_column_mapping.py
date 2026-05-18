"""add upload column mapping

Revision ID: 0002_upload_column_mapping
Revises: 0001_initial_models
Create Date: 2026-05-19
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_upload_column_mapping"
down_revision = "0001_initial_models"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "upload_jobs",
        sa.Column("column_mapping_json", sa.Text(), nullable=False, server_default="{}"),
    )
    op.alter_column("upload_jobs", "column_mapping_json", server_default=None)


def downgrade() -> None:
    op.drop_column("upload_jobs", "column_mapping_json")
