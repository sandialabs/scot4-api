import meilisearch
from typing import Any, Annotated
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session

from app import crud, models
from app.api import deps
from app.core.config import settings
from app.schemas import SearchRequest
from app.utils import create_schema_details

router = APIRouter()


description, examples = create_schema_details(SearchRequest)


@router.post("/", description=description)
def search(
    *,
    search_text: Annotated[SearchRequest, Body(..., openapi_examples=examples)],
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_user),
    roles: list[models.Role] = Depends(deps.get_current_roles),
) -> Any:
    """
    Searches meilisearch
    """

    client = meilisearch.Client(settings.SEARCH_HOST, settings.SEARCH_API_KEY)
    entries_index = client.index('entries')
    entries_hits = entries_index.search(
        search_text.text,
        {
            'attributesToHighlight': ['entry_text', 'parent_text'],
            'highlightPreTag': '<mark>',
            'cropLength': 30,
            'highlightPostTag': '</mark>',
            'limit': 100,
            'attributesToCrop': ['entry_text']
        }
    )
    all_hits = {}
    permission_check = []
    for hit in entries_hits['hits']:
        if all_hits.get(f"{hit['target_type']}-{hit['target_id']}") is None:
            all_hits[f"{hit['target_type']}-{hit['target_id']}"] = [hit]
        else:
            all_hits[f"{hit['target_type']}-{hit['target_id']}"].append(hit)
        permission_check.append({'id': hit['target_id'], 'type': hit['target_type']})
    filter_list = crud.permission.filter_search_hits(db, permission_check, roles)
    if filter_list is False:
        filtered_results = []
        for k, v in all_hits.items():
            filtered_results.extend([x['_formatted'] for x in v])
        return filtered_results
    else:
        filter_list = [f"{x[0].value}-{x[1]}" for x in filter_list]
        filtered_results = []
        for k, v in all_hits.items():
            if k in filter_list:
                filtered_results.extend([x['_formatted'] for x in v])
        return filtered_results
