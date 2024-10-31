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
    generic_export
)

router = APIRouter()

# Create get, post, put, delete, entries, tag, and source endpoints
generic_export(router, crud.vuln_feed, TargetTypeEnum.vuln_feed)
generic_get(router, crud.vuln_feed, TargetTypeEnum.vuln_feed, schemas.VulnFeed)
generic_post(
    router, crud.vuln_feed, TargetTypeEnum.vuln_feed, schemas.VulnFeed, schemas.VulnFeedCreate
)
generic_put(
    router, crud.vuln_feed, TargetTypeEnum.vuln_feed, schemas.VulnFeed, schemas.VulnFeedUpdate
)
generic_delete(router, crud.vuln_feed, TargetTypeEnum.vuln_feed, schemas.VulnFeed)
generic_undelete(router, crud.vuln_feed, TargetTypeEnum.vuln_feed, schemas.VulnFeed)
generic_entries(router, TargetTypeEnum.vuln_feed)
generic_tag_untag(router, crud.vuln_feed, TargetTypeEnum.vuln_feed, schemas.VulnFeed)
generic_source_add_remove(router, crud.vuln_feed, TargetTypeEnum.vuln_feed, schemas.VulnFeed)
generic_entities(router, TargetTypeEnum.vuln_feed)
generic_files(router, TargetTypeEnum.vuln_feed)
generic_history(router, crud.vuln_feed, TargetTypeEnum.vuln_feed)
generic_search(router, crud.vuln_feed, TargetTypeEnum.vuln_feed, schemas.VulnFeedSearch, schemas.VulnFeed)
