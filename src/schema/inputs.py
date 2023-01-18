from typing import Optional

import strawberry
from lcacollect_config.graphql.input_filters import BaseFilter, FilterOptions, SortOptions


@strawberry.input
class SchemaTemplateFilters(BaseFilter):
    name: Optional[FilterOptions] = None
    id: Optional[FilterOptions] = None


@strawberry.input
class SchemaTemplateSort(BaseFilter):
    name: Optional[FilterOptions] = None
    id: Optional[FilterOptions] = None


@strawberry.input
class ProjectSourceFilters(BaseFilter):
    name: Optional[FilterOptions] = None
    project_id: Optional[FilterOptions] = None
    id: Optional[FilterOptions] = None


@strawberry.input
class ReportingSchemaFilters(BaseFilter):
    name: Optional[FilterOptions] = None
    id: Optional[FilterOptions] = None
    project_id: Optional[FilterOptions] = None


@strawberry.input
class ReportingSchemaSort(BaseFilter):
    name: Optional[FilterOptions] = None
    id: Optional[FilterOptions] = None
    description: Optional[FilterOptions] = None


@strawberry.input
class SchemaCategoryFilters(BaseFilter):
    name: Optional[FilterOptions] = None
    id: Optional[FilterOptions] = None
    description: Optional[FilterOptions] = None


@strawberry.input
class SchemaCategorySort(BaseFilter):
    name: Optional[FilterOptions] = None
    id: Optional[FilterOptions] = None
    description: Optional[FilterOptions] = None


@strawberry.input
class SchemaElementFilters(BaseFilter):
    id: Optional[FilterOptions] = None
    name: Optional[FilterOptions] = None
    classification: Optional[FilterOptions] = None
    subclassification: Optional[FilterOptions] = None
    quantity: Optional[FilterOptions] = None
    unit: Optional[FilterOptions] = None
    description: Optional[FilterOptions] = None
    # version: str | None
    # origin_id: str | None


@strawberry.input
class SchemaElementSort(BaseFilter):
    id: Optional[FilterOptions] = None
    name: Optional[FilterOptions] = None
    classification: Optional[FilterOptions] = None
    subclassification: Optional[FilterOptions] = None
    quantity: Optional[FilterOptions] = None
    unit: Optional[FilterOptions] = None
    description: Optional[FilterOptions] = None


@strawberry.input
class CommitFilters(BaseFilter):
    id: Optional[FilterOptions] = None
    short_id: Optional[FilterOptions] = None
    added: Optional[FilterOptions] = None


@strawberry.input
class CommitSort(BaseFilter):
    id: Optional[SortOptions] = None
    short_id: Optional[SortOptions] = None
    added: Optional[SortOptions] = None


@strawberry.input
class TagFilters(BaseFilter):
    id: Optional[FilterOptions] = None
    short_id: Optional[FilterOptions] = None
    added: Optional[FilterOptions] = None
    author_id: Optional[FilterOptions] = None


@strawberry.input
class CommitSort(BaseFilter):
    id: Optional[SortOptions] = None
    short_id: Optional[SortOptions] = None
    added: Optional[SortOptions] = None


@strawberry.input
class TaskFilters(BaseFilter):
    id: Optional[FilterOptions] = None
    description: Optional[FilterOptions] = None
    due_date: Optional[FilterOptions] = None
    name: Optional[FilterOptions] = None
    item_id: Optional[FilterOptions] = None
    item_type: Optional[FilterOptions] = None


@strawberry.input
class CommentFilters(BaseFilter):
    id: Optional[FilterOptions] = None
    added: Optional[FilterOptions] = None
    text: Optional[FilterOptions] = None
