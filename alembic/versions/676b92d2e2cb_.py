"""empty message

Revision ID: 676b92d2e2cb
Revises: 90adf54af5ad
Create Date: 2024-03-04 10:44:56.385686

"""
import sqlalchemy as sa
import sqlmodel
from alembic import op

import models.schema_category as models_category
import models.typecode as models_typecode

# revision identifiers, used by Alembic.
revision = "676b92d2e2cb"
down_revision = "90adf54af5ad"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "schemacategory", sa.Column("type_code_element_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True)
    )
    op.create_foreign_key(
        "schemacategory_typecodeelement_fkey", "schemacategory", "typecodeelement", ["type_code_element_id"], ["id"]
    )
    op.add_column("schematemplate", sa.Column("domain", sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column("typecode", sa.Column("domain", sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    # ### end Alembic commands ###

    # bind = op.get_bind()
    # session = sa.orm.Session(bind=bind)

    # for category in session.query(models_category.SchemaCategory):
    #     code, name = category.name.split("|")
    #     level = len(category.path.split("/"))
    #     type_code_element = models_typecode.TypeCodeElement(
    #         code=code,
    #         name=name,
    #         level=level,
    #         parent_path=category.path,
    #     )
    #     category.type_code_element = type_code_element
    #     session.add(category)

    # session.commit()

    op.drop_column("schemacategory", "path")
    op.drop_column("schemacategory", "name")


def downgrade():
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)

    for category in session.query(models_category.SchemaCategory).options(
        sa.orm.selectinload(models_category.SchemaCategory.type_code_element)
    ):
        category.name = f"{category.type_code_element.code}|{category.type_code_element.name}"
        category.path = category.type_code_element.path
        session.add(category)

    session.commit()

    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("typecode", "domain")
    op.drop_column("schematemplate", "domain")
    op.add_column("schemacategory", sa.Column("name", sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column("schemacategory", sa.Column("path", sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_constraint("schemacategory_typecodeelement_fkey", "schemacategory", type_="foreignkey")
    op.drop_column("schemacategory", "type_code_element_id")
    # ### end Alembic commands ###
