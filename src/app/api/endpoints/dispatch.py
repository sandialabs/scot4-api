from fastapi import APIRouter

from app import crud, schemas
from app.enums import TargetTypeEnum

from .generic import (
    generic_delete,
    generic_entities,
    generic_entries,
    generic_get,
    generic_post,
    generic_put,
    generic_source_add_remove,
    generic_tag_untag,
    generic_undelete,
    generic_history,
    generic_search,
    generic_export,
    generic_upvote_and_downvote,
    generic_user_links
)

router = APIRouter()

# Create get, post, put, delete, entries, tag, and source endpoints
generic_get(router, crud.dispatch, TargetTypeEnum.dispatch, schemas.Dispatch)
generic_post(router, crud.dispatch, TargetTypeEnum.dispatch, schemas.Dispatch, schemas.DispatchCreate)
generic_put(router, crud.dispatch, TargetTypeEnum.dispatch, schemas.Dispatch, schemas.DispatchUpdate)
generic_delete(router, crud.dispatch, TargetTypeEnum.dispatch, schemas.Dispatch)
generic_search(router, crud.dispatch, TargetTypeEnum.dispatch, schemas.DispatchSearch, schemas.Dispatch)
generic_undelete(router, crud.dispatch, TargetTypeEnum.dispatch, schemas.Dispatch)
generic_entries(router, TargetTypeEnum.dispatch)
generic_tag_untag(router, crud.dispatch, TargetTypeEnum.dispatch, schemas.Dispatch)
generic_source_add_remove(router, crud.dispatch, TargetTypeEnum.dispatch, schemas.Dispatch)
generic_entities(router, TargetTypeEnum.dispatch)
generic_history(router, crud.dispatch, TargetTypeEnum.dispatch)
generic_export(router, crud.dispatch, TargetTypeEnum.dispatch)
generic_upvote_and_downvote(router, crud.dispatch, TargetTypeEnum.dispatch, schemas.Dispatch)
generic_user_links(router, crud.dispatch, TargetTypeEnum.dispatch, schemas.Dispatch)
