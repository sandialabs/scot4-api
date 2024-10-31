from fastapi import APIRouter

from app import crud, schemas
from app.enums import TargetTypeEnum

from .generic import (
    generic_delete,
    generic_get,
    generic_post,
    generic_put,
    generic_history,
    generic_entries,
    generic_entities,
    generic_search,
    generic_export
)

router = APIRouter()

# Create get, post, put, and delete endpoints
generic_export(router, crud.feed, TargetTypeEnum.feed)
generic_get(router, crud.feed, TargetTypeEnum.feed, schemas.Feed)
generic_post(
    router, crud.feed, TargetTypeEnum.feed, schemas.Feed, schemas.FeedCreate
)
generic_put(
    router, crud.feed, TargetTypeEnum.feed, schemas.Feed, schemas.FeedUpdate
)
generic_delete(router, crud.feed, TargetTypeEnum.feed, schemas.Feed)
generic_history(router, crud.feed, TargetTypeEnum.feed)
generic_entries(router, TargetTypeEnum.feed)
generic_entities(router, TargetTypeEnum.feed)
generic_search(router, crud.feed, TargetTypeEnum.feed, schemas.FeedSearch, schemas.Feed)
