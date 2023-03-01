"""empty message

Revision ID: 03de9c8dfbb7
Revises: e182d22faf5f
Create Date: 2022-10-07 14:05:49.946317

"""
import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision = "03de9c8dfbb7"
down_revision = "e182d22faf5f"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("commit", "repository_id", existing_type=sa.VARCHAR(), nullable=False)
    op.drop_column("schemacategory", "project_id")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "schemacategory",
        sa.Column("project_id", sa.VARCHAR(), autoincrement=False, nullable=False),
    )
    op.alter_column("commit", "repository_id", existing_type=sa.VARCHAR(), nullable=True)
    # ### end Alembic commands ###
