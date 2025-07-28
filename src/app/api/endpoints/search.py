import meilisearch
from typing import Any, Annotated
from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.orm import Session

from app import crud, models
from app.api import deps
from app.enums import TargetTypeEnum
from app.core.config import settings
from app.schemas import SearchRequest
from app.utils import create_schema_details, get_search_filters

router = APIRouter()


description, _ = create_schema_details(SearchRequest, "Perform a search across all SCOT text data (entries, alerts, and titles), optionally filtering by certain fields of the parent object")


def generate_single_list_or_range(name: str, value: str | list | tuple):
    if isinstance(value, list):
        return f"{name} IN {str(value)}"
    elif isinstance(value, tuple):
        return f"{name} >= {value[0]} AND {name} <= {value[1]}"
    elif isinstance(value, str):
        escaped_value = value.replace("'", "\\'")
        return f"{name} = '{escaped_value}'"
    else:
        return f"{name} = '{value}'"


@router.post("/", summary="Perform a text search", description=description)
def search(
    *,
    search_body: Annotated[SearchRequest, Body(...)],
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_user),
    roles: list[models.Role] = Depends(deps.get_current_roles),
) -> Any:
    """
    Searches meilisearch
    """

    client = meilisearch.Client(settings.SEARCH_HOST, settings.SEARCH_API_KEY)
    entries_index = client.index('entries')

    search_dict = get_search_filters(search_body)
    search_filter = []
    for key in search_dict:
        if key not in ["text", "sort", "not"]:
            search_filter.append(generate_single_list_or_range(key, search_dict[key]))
    for key in search_dict.get("not", []):
        if key not in ["text", "sort"]:
            search_filter.append("NOT (" + generate_single_list_or_range(key, search_dict["not"][key]) + ")")

    sortable = ['entry_id', 'target_type', 'target_id', 'created', 'modified',
                'owner', 'popularity_count']
    sort_order = []
    if 'sort' in search_dict:
        if not isinstance(search_dict['sort'], list):
            search_dict['sort'] = [search_dict['sort']]
        for s in search_dict['sort']:
            if s in sortable:
                sort_order.append(s + ":asc")
            elif isinstance(s, str) and s.startswith("-") and s[1:] in sortable:
                sort_order.append(s[1:] + ":desc")
            elif isinstance(s, str) and s.startswith("+") and s[1:] in sortable:
                sort_order.append(s[1:] + ":asc")
            else:
                raise HTTPException(422, f'"{s}" is not a sortable search field')

    entries_hits = entries_index.search(
        search_body.text,
        {
            'attributesToHighlight': ['entry_text', 'parent_text'],
            'highlightPreTag': '<mark>',
            'cropLength': 30,
            'highlightPostTag': '</mark>',
            'limit': 100,
            'attributesToCrop': ['entry_text'],
            'filter': search_filter,
            'sort': sort_order
        }
    )
    # Look up user's effective permissions on every item in the search result
    all_hits = {}
    permission_check = []
    for hit in entries_hits['hits']:
        if all_hits.get(f"{hit['target_type']}-{hit['target_id']}") is None:
            all_hits[f"{hit['target_type']}-{hit['target_id']}"] = [hit]
        else:
            all_hits[f"{hit['target_type']}-{hit['target_id']}"].append(hit)
        permission_check.append({'id': hit['target_id'], 'type': hit['target_type']})
        if hit["target_type"] != TargetTypeEnum.alertgroup.value:
            permission_check.append({'id': hit['entry_id'], 'type': TargetTypeEnum.entry.value})
    filter_list = crud.permission.filter_search_hits(db, permission_check, roles)
    if filter_list is False:
        # User is an admin, don't check permissions
        filtered_results = []
        for k, v in all_hits.items():
            filtered_results.extend([x['_formatted'] for x in v])
        return filtered_results
    else:
        # Check permissions on each target type/id pair in the result
        filter_list = [f"{x[0].value}-{x[1]}" for x in filter_list]
        filtered_results = []
        for k, v in all_hits.items():
            if k in filter_list:
                # Only include results from an item if user has permissions on that item
                for x in v:
                    if x["target_type"] == TargetTypeEnum.alertgroup.value:
                        # Alerts don't have separate permissions from alertgroups
                        filtered_results.append(x['_formatted'])
                    elif f"entry-{x['entry_id']}" in filter_list:
                        # Only include in results if user also has permission on entry
                        filtered_results.append(x['_formatted'])
        return filtered_results
