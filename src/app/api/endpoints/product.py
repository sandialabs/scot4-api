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
    generic_files,
    generic_search,
    generic_export,
    generic_upvote_and_downvote,
    generic_user_links
)

router = APIRouter()

# Create get, post, put, delete, entries, tag, and source endpoints
generic_get(router, crud.product, TargetTypeEnum.product, schemas.Product)
generic_post(router, crud.product, TargetTypeEnum.product, schemas.Product, schemas.ProductCreate)
generic_put(router, crud.product, TargetTypeEnum.product, schemas.Product, schemas.ProductUpdate)
generic_delete(router, crud.product, TargetTypeEnum.product, schemas.Product)
generic_search(router, crud.product, TargetTypeEnum.product, schemas.ProductSearch, schemas.Product)
generic_undelete(router, crud.product, TargetTypeEnum.product, schemas.Product)
generic_entries(router, TargetTypeEnum.product)
generic_tag_untag(router, crud.product, TargetTypeEnum.product, schemas.Product)
generic_source_add_remove(router, crud.product, TargetTypeEnum.product, schemas.Product)
generic_entities(router, TargetTypeEnum.product)
generic_history(router, crud.product, TargetTypeEnum.product)
generic_export(router, crud.product, TargetTypeEnum.product)
generic_files(router, TargetTypeEnum.product)
generic_upvote_and_downvote(router, crud.product, TargetTypeEnum.product, schemas.Product)
generic_user_links(router, crud.product, TargetTypeEnum.product, schemas.Product)
