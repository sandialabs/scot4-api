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
generic_export(router, crud.vuln_track, TargetTypeEnum.vuln_track)
generic_get(router, crud.vuln_track, TargetTypeEnum.vuln_track, schemas.VulnTrack)
generic_post(router, crud.vuln_track, TargetTypeEnum.vuln_track, schemas.VulnTrack, schemas.VulnTrackCreate)
generic_put(router, crud.vuln_track, TargetTypeEnum.vuln_track, schemas.VulnTrack, schemas.VulnTrackUpdate)
generic_delete(router, crud.vuln_track, TargetTypeEnum.vuln_track, schemas.VulnTrack)
generic_undelete(router, crud.vuln_track, TargetTypeEnum.vuln_track, schemas.VulnTrack)
generic_entries(router, TargetTypeEnum.vuln_track)
generic_tag_untag(router, crud.vuln_track, TargetTypeEnum.vuln_track, schemas.VulnTrack)
generic_source_add_remove(router, crud.vuln_track, TargetTypeEnum.vuln_track, schemas.VulnTrack)
generic_entities(router, TargetTypeEnum.vuln_track)
generic_files(router, TargetTypeEnum.vuln_track)
generic_history(router, crud.vuln_track, TargetTypeEnum.vuln_track)
generic_search(router, crud.vuln_track, TargetTypeEnum.vuln_track, schemas.VulnTrackSearch, schemas.VulnTrack)
generic_upvote_and_downvote(router, crud.vuln_track, TargetTypeEnum.vuln_track, schemas.VulnTrack)
generic_user_links(router, crud.vuln_track, TargetTypeEnum.vuln_track, schemas.VulnTrack)
