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
    with op.batch_alter_table("upload_jobs") as batch_op:
        batch_op.add_column(
            sa.Column("column_mapping_json", sa.Text(), nullable=False, server_default="{}")
        )
        batch_op.alter_column("column_mapping_json", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("upload_jobs") as batch_op:
        batch_op.drop_column("column_mapping_json")
