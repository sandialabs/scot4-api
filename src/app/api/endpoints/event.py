from fastapi import APIRouter

from app import crud, schemas
from app.enums import TargetTypeEnum

from .generic import (
    generic_delete,
    generic_entities,
    generic_entries,
    generic_files,
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
generic_get(router, crud.event, TargetTypeEnum.event, schemas.Event)
generic_post(router, crud.event, TargetTypeEnum.event, schemas.Event, schemas.EventCreate)
generic_put(router, crud.event, TargetTypeEnum.event, schemas.Event, schemas.EventUpdate)
generic_delete(router, crud.event, TargetTypeEnum.event, schemas.Event)
generic_search(router, crud.event, TargetTypeEnum.event, schemas.EventSearch, schemas.Event)
generic_undelete(router, crud.event, TargetTypeEnum.event, schemas.Event)
generic_entries(router, TargetTypeEnum.event)
generic_tag_untag(router, crud.event, TargetTypeEnum.event, schemas.Event)
generic_source_add_remove(router, crud.event, TargetTypeEnum.event, schemas.Event)
generic_entities(router, TargetTypeEnum.event)
generic_history(router, crud.event, TargetTypeEnum.event)
generic_export(router, crud.event, TargetTypeEnum.event)
generic_files(router, TargetTypeEnum.event)
generic_upvote_and_downvote(router, crud.event, TargetTypeEnum.event, schemas.Event)
generic_user_links(router, crud.event, TargetTypeEnum.event, schemas.Event)
