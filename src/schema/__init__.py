from inspect import getdoc

import strawberry
from lcacollect_config.permissions import IsAuthenticated

import schema.comment as schema_comment
import schema.commit as schema_commit
import schema.export as schema_export
import schema.reporting_schema as schema_reporting
import schema.schema_category as schema_category
import schema.schema_element as schema_element
import schema.schema_template as schema_template
import schema.source as schema_source
import schema.tag as schema_tag
import schema.task as schema_task
from core import federation


@strawberry.type
class Query:

    """GraphQL Queries"""

    project_sources: list[schema_source.GraphQLProjectSource] = strawberry.field(
        permission_classes=[IsAuthenticated],
        resolver=schema_source.project_sources_query,
        description=getdoc(schema_source.project_sources_query),
    )

    # Reporting Schema
    schema_templates: list[schema_template.GraphQLSchemaTemplate] = strawberry.field(
        permission_classes=[IsAuthenticated],
        resolver=schema_template.query_schema_templates,
        description=getdoc(schema_template.query_schema_templates),
    )
    reporting_schemas: list[schema_reporting.GraphQLReportingSchema] = strawberry.field(
        permission_classes=[IsAuthenticated],
        resolver=schema_reporting.query_reporting_schemas,
        description=getdoc(schema_reporting.query_reporting_schemas),
    )
    schema_categories: list[schema_category.GraphQLSchemaCategory] = strawberry.field(
        permission_classes=[IsAuthenticated],
        resolver=schema_category.query_schema_categories,
        description=getdoc(schema_category.query_schema_categories),
    )
    schema_elements: list[schema_element.GraphQLSchemaElement] = strawberry.field(
        permission_classes=[IsAuthenticated],
        resolver=schema_element.query_schema_elements,
        description=getdoc(schema_element.query_schema_elements),
    )
    commits: list[schema_commit.GraphQLCommit] = strawberry.field(
        permission_classes=[IsAuthenticated],
        resolver=schema_commit.query_commits,
        description=getdoc(schema_commit.query_commits),
    )
    tags: list[schema_tag.GraphQLTag] = strawberry.field(
        permission_classes=[IsAuthenticated],
        resolver=schema_tag.query_tags,
        description=getdoc(schema_tag.query_tags),
    )
    tasks: list[schema_task.GraphQLTask] = strawberry.field(
        permission_classes=[IsAuthenticated],
        resolver=schema_task.query_tasks,
        description=getdoc(schema_task.query_tasks),
    )
    comments: list[schema_comment.GraphQLComment] = strawberry.field(
        permission_classes=[IsAuthenticated],
        resolver=schema_comment.query_comments,
        description=getdoc(schema_comment.query_comments),
    )
    export_reporting_schema: str = strawberry.field(
        permission_classes=[IsAuthenticated],
        resolver=schema_export.export_reporting_schema_mutation,
        description=getdoc(schema_export.export_reporting_schema_mutation),
    )


@strawberry.type
class Mutation:

    """GraphQL Mutations"""

    # Schema Template
    add_schema_template: schema_template.GraphQLSchemaTemplate = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_template.add_schema_template_mutation,
        description=getdoc(schema_template.add_schema_template_mutation),
    )
    update_schema_template: schema_template.GraphQLSchemaTemplate = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_template.update_schema_template_mutation,
        description=getdoc(schema_template.update_schema_template_mutation),
    )
    delete_schema_template: str = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_template.delete_schema_template_mutation,
        description=getdoc(schema_template.delete_schema_template_mutation),
    )

    # Reporting Schema
    add_reporting_schema: schema_reporting.GraphQLReportingCreationSchema = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_reporting.add_reporting_schema_mutation,
        description=getdoc(reporting_schema.add_reporting_schema_mutation),
    )
    add_reporting_schema_from_template: schema_reporting.GraphQLReportingCreationSchema = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_reporting.add_reporting_schema_from_template_mutation,
        description=getdoc(reporting_schema.add_reporting_schema_mutation),
    )
    update_reporting_schema: schema_reporting.GraphQLReportingSchema = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_reporting.update_reporting_schema_mutation,
        description=getdoc(reporting_schema.update_reporting_schema_mutation),
    )
    delete_reporting_schema: str = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_reporting.delete_reporting_schema_mutation,
        description=getdoc(reporting_schema.delete_reporting_schema_mutation),
    )

    # Schema Category
    add_schema_category: schema_category.GraphQLSchemaCategory = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_category.add_schema_category_mutation,
        description=getdoc(schema_category.add_schema_category_mutation),
    )
    update_schema_category: schema_category.GraphQLSchemaCategory = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_category.update_schema_category_mutation,
        description=getdoc(schema_category.update_schema_category_mutation),
    )
    delete_schema_category: str = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_category.delete_schema_category_mutation,
        description=getdoc(schema_category.delete_schema_category_mutation),
    )

    # Schema Element
    add_schema_element: schema_element.GraphQLSchemaElement = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_element.add_schema_element_mutation,
        description=getdoc(schema_element.add_schema_element_mutation),
    )
    add_schema_element_from_source: list[schema_element.GraphQLSchemaElement] = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_element.add_schema_element_from_source_mutation,
        description=getdoc(schema_element.add_schema_element_mutation),
    )
    update_schema_elements: list[schema_element.GraphQLSchemaElement] = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_element.update_schema_elements_mutation,
        description=getdoc(schema_element.update_schema_elements_mutation),
    )
    delete_schema_element: str = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_element.delete_schema_element_mutation,
        description=getdoc(schema_element.delete_schema_element_mutation),
    )

    # Project Source
    add_project_source: schema_source.GraphQLProjectSource = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_source.add_project_source_mutation,
        description=getdoc(schema_source.add_project_source_mutation),
    )

    update_project_source: schema_source.GraphQLProjectSource = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_source.update_project_source_mutation,
        description=getdoc(schema_source.update_project_source_mutation),
    )
    delete_project_source: str = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_source.delete_project_source_mutation,
        description=getdoc(schema_source.delete_project_source_mutation),
    )

    # Tasks
    add_task: schema_task.GraphQLTask = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_task.add_task_mutation,
        description=getdoc(schema_task.add_task_mutation),
    )
    update_task: schema_task.GraphQLTask = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_task.update_task_mutation,
        description=getdoc(schema_task.update_task_mutation),
    )
    delete_task: str = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_task.delete_task_mutation,
        description=getdoc(schema_task.delete_task_mutation),
    )

    # Comments
    add_comment: schema_comment.GraphQLComment = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_comment.add_comment_mutation,
        description=getdoc(schema_comment.add_comment_mutation),
    )
    update_comment: schema_comment.GraphQLComment = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_comment.update_comment_mutation,
        description=getdoc(schema_comment.update_comment_mutation),
    )
    delete_comment: str = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_comment.delete_comment_mutation,
        description=getdoc(schema_comment.delete_comment_mutation),
    )

    # Tags
    create_tag: schema_tag.GraphQLTag = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_tag.create_tag,
        description=getdoc(schema_tag.create_tag),
    )
    update_tag: schema_tag.GraphQLTag = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_tag.update_tag,
        description=getdoc(schema_tag.update_tag),
    )
    delete_tag: str = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_tag.delete_tag,
        description=getdoc(schema_tag.delete_tag),
    )


schema = strawberry.federation.Schema(
    query=Query,
    mutation=Mutation,
    enable_federation_2=True,
    types=[federation.GraphQLProjectMember],
)
