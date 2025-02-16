"""Add new table with relationship

Revision ID: 49ea96a793f8
Revises: 58c0a90936d6
Create Date: 2021-09-08 16:26:58.692504

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = "2cda5f1bc8d4"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()
    if "refresh_dataset_datastore" in tables:
        return

    op.create_table(
        "refresh_dataset_datastore",
        sa.Column("id", sa.UnicodeText, primary_key=True),
        sa.Column(
            "dataset_id",
            sa.UnicodeText,
            sa.ForeignKey("package.id"),
            nullable=False,
        ),
        sa.Column("frequency", sa.UnicodeText, nullable=False),
        sa.Column(
            "created_user_id",
            sa.UnicodeText,
            sa.ForeignKey("user.id"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column("datastore_last_refreshed", sa.DateTime, nullable=True),
    )


def downgrade():
    op.drop_table("refresh_dataset_datastore")
