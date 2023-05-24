"""empty message

Revision ID: 54ca42dc1db2
Revises: f0a2b62bfe5a
Create Date: 2022-11-03 10:11:34.002913

"""
import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision = "54ca42dc1db2"
down_revision = "f0a2b62bfe5a"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("projectsource", "author_id", existing_type=sa.VARCHAR(), nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("projectsource", "author_id", existing_type=sa.VARCHAR(), nullable=False)
    # ### end Alembic commands ###
