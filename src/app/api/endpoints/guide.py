from typing import Any, Annotated
from fastapi import APIRouter, Depends, Path, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.enums import TargetTypeEnum, PermissionEnum

from .generic import (
    generic_delete,
    generic_entries,
    generic_get,
    generic_post,
    generic_put,
    generic_source_add_remove,
    generic_tag_untag,
    generic_undelete,
    generic_history,
    generic_entities,
    generic_search,
    generic_export,
    generic_upvote_and_downvote,
    generic_user_links,
    generic_get_signatures
)

router = APIRouter()

# Create get, post, put, and delete endpoints
generic_get(router, crud.guide, TargetTypeEnum.guide, schemas.Guide)
generic_post(router, crud.guide, TargetTypeEnum.guide, schemas.Guide, schemas.GuideCreate)
generic_put(router, crud.guide, TargetTypeEnum.guide, schemas.Guide, schemas.GuideUpdate)
generic_delete(router, crud.guide, TargetTypeEnum.guide, schemas.Guide)
generic_search(router, crud.guide, TargetTypeEnum.guide, schemas.GuideSearch, schemas.Guide)
generic_undelete(router, crud.guide, TargetTypeEnum.guide, schemas.Guide)
generic_entries(router, TargetTypeEnum.guide)
generic_tag_untag(router, crud.guide, TargetTypeEnum.guide, schemas.Guide)
generic_source_add_remove(router, crud.guide, TargetTypeEnum.guide, schemas.Guide)
generic_entities(router, TargetTypeEnum.guide)
generic_history(router, crud.guide, TargetTypeEnum.guide)
generic_export(router, crud.guide, TargetTypeEnum.guide)
generic_upvote_and_downvote(router, crud.guide, TargetTypeEnum.guide, schemas.Guide)
generic_user_links(router, crud.guide, TargetTypeEnum.guide, schemas.Guide)
generic_get_signatures(router, crud.guide, TargetTypeEnum.guide)
