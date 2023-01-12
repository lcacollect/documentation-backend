# import pytest
# from models.schema_template import schema
# from sqlmodel.ext.asyncio.session import AsyncSession
#
#
# @pytest.mark.asyncio
# async def test_get_schema_templates(schema_templates, db):
#     query = f"""
#         query {{
#             schemaTemplates() {{
#                 name
#                 id
#                 template
#             }}
#         }}
#     """
#
#     async with AsyncSession(db) as session:
#         response = await schema.execute(query, context_value={"session": session, "user": True})
#
#     assert response.errors is None
#     assert response.data["schemaTemplates"] == [
#         {
#             "name": f"schemaTemplate {i}",
#             "id": "My Category",
#         }
#         for i in range(3)
#     ]
#
