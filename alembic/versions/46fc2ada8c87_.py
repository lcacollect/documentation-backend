"""empty message

Revision ID: 46fc2ada8c87
Revises: 74b203c08b1f
Create Date: 2022-11-30 16:15:01.339109

"""
import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision = "46fc2ada8c87"
down_revision = "74b203c08b1f"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("schemaelement", sa.Column("quantity", sa.Float(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("schemaelement", "quantity")
    # ### end Alembic commands ###
