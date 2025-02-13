from fastapi import APIRouter

from app import crud, schemas
from app.enums import TargetTypeEnum

from .generic import (
    generic_delete,
    generic_get,
    generic_post,
    generic_put,
    generic_tag_untag,
    generic_undelete,
    generic_search,
    generic_upvote_and_downvote,
    generic_user_links
)

router = APIRouter()

# Create get, post, put, delete, and tag endpoints
generic_get(router, crud.checklist, TargetTypeEnum.checklist, schemas.Checklist)
generic_post(router, crud.checklist, TargetTypeEnum.checklist, schemas.Checklist, schemas.ChecklistCreate)
generic_put(router, crud.checklist, TargetTypeEnum.checklist, schemas.Checklist, schemas.ChecklistUpdate)
generic_delete(router, crud.checklist, TargetTypeEnum.checklist, schemas.Checklist)
generic_undelete(router, crud.checklist, TargetTypeEnum.checklist, schemas.Checklist)
generic_tag_untag(router, crud.checklist, TargetTypeEnum.checklist, schemas.Checklist)
generic_search(router, crud.checklist, TargetTypeEnum.checklist, schemas.ChecklistSearch, schemas.Checklist)
generic_upvote_and_downvote(router, crud.checklist, TargetTypeEnum.checklist, schemas.Checklist)
generic_user_links(router, crud.checklist, TargetTypeEnum.checklist, schemas.Checklist)
