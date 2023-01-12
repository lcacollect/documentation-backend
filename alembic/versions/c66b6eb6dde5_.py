"""empty message

Revision ID: c66b6eb6dde5
Revises: b4cc2175c7d0
Create Date: 2022-10-24 11:10:45.381935

"""
import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision = "c66b6eb6dde5"
down_revision = "4793e7af27f7"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "task",
        sa.Column("assignee_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )
    op.add_column(
        "task",
        sa.Column(
            "assigned_group_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("task", "assigned_group_id")
    op.drop_column("task", "assignee_id")
    # ### end Alembic commands ###
