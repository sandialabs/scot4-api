import hashlib
import time
import random
import string
from typing import Annotated
from datetime import datetime
from urllib.parse import quote
from streaming_form_data import StreamingFormDataParser
from streaming_form_data.targets import SHA256Target
from fastapi import (
    Request,
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Body,
    Path
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.enums import PermissionEnum, TargetTypeEnum, TlpEnum
from app.object_storage.base import FileSizeTarget

from .generic import (
    generic_get,
    generic_put,
    generic_source_add_remove,
    generic_tag_untag,
    generic_history,
    generic_search
)

router = APIRouter()

# Create get, post, put, tag, source, and history endpoints
generic_get(router, crud.file, TargetTypeEnum.file, schemas.File)
generic_put(router, crud.file, TargetTypeEnum.file, schemas.File, schemas.FileUpdate)
generic_tag_untag(router, crud.file, TargetTypeEnum.file, schemas.File)
generic_source_add_remove(router, crud.file, TargetTypeEnum.file, schemas.File)
generic_history(router, crud.file, TargetTypeEnum.file)
generic_search(router, crud.file, TargetTypeEnum.file, schemas.FileSearch, schemas.File)


@router.post("/", response_model=schemas.File)
async def create_file(
    *,
    db: Session = Depends(deps.get_db),
    request: Request,
    current_user: models.User = Depends(deps.get_current_active_user),
    current_roles: list[models.Role] = Depends(deps.get_current_roles),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    """
    Upload a file; if target_type and target_id are provided, the file will
    be attached to the specified object (and have its same permissions)
    """

    letters = string.ascii_lowercase
    nonce = "".join(random.choices(letters, k=30))  # nosec
    file_reference_id = hashlib.sha256(f"{current_user.username}:{time.time()}:{nonce}".encode('utf-8')).hexdigest()
    target_id = request.headers.get('target_id')
    target_type = request.headers.get('target_type')
    if target_type is not None:
        target_type = target_type.lower()
    if target_id is not None and target_type is not None:
        if not deps.PermissionCheckId(target_type, PermissionEnum.modify)(
                target_id, db, current_user, current_roles
        ):
            raise HTTPException(403, f"You do not have permission to create a file in {target_type} {target_id}")
        if target_type is None:
            raise HTTPException(403, "Must provide target type and id")

    try:
        scot_file_target = crud.file.get_storage_target(db_session=db, file_pointer=file_reference_id)
        parser = StreamingFormDataParser(headers=request.headers)
        sha_256 = SHA256Target()
        filesize = FileSizeTarget()
        parser.register('file', scot_file_target)
        parser.register('file', sha_256)  # The file name is going to be the hex digest of the sha256.
        parser.register('file', filesize)  # get a more accurate file size
        async for chunk in request.stream():
            parser.data_received(chunk)

        obj_in = schemas.FileCreate(
            owner=current_user.username,
            content_type=sha_256.multipart_content_type,
            filename=sha_256.multipart_filename,
            filesize=filesize.filesize,
            sha256=sha_256._hash.hexdigest(),
            file_pointer=file_reference_id
        )
        if target_type is not None and target_id is not None:
            created_file_obj = crud.file.create_in_object(db,
                                                          obj_in=obj_in,
                                                          source_type=target_type,
                                                          source_id=target_id,
                                                          audit_logger=audit_logger
                                                          )
        else:
            created_file_obj = crud.file.create(
                db_session=db, obj_in=obj_in, audit_logger=audit_logger
            )
        return created_file_obj
    except Exception as e:
        raise HTTPException(422, str(e))


# Download the actual file"
@router.get("/download/{id}")
def download_file(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    current_roles: list[models.Role] = Depends(deps.get_current_roles),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    fileobj = crud.file.get(db, id, audit_logger=audit_logger)
    if not fileobj:
        raise HTTPException(404, "File not found")
    try:
        filestream = crud.file.get_content(db, fileobj)
    except Exception as e:
        raise HTTPException(500, f"Could not retrieve file data from storage - {str(e)}")
    encoded_name = "UTF-8''" + quote(fileobj.filename.encode("utf-8"))

    return StreamingResponse(
        filestream,
        media_type=fileobj.content_type,
        headers={"content-disposition": "attachment; filename*=%s" % encoded_name},
    )


delete_dep = Depends(deps.PermissionCheckId(TargetTypeEnum.file, PermissionEnum.delete))


@router.delete("/{id}", response_model=schemas.File, dependencies=[delete_dep])
def delete_files(
    *,
    id: Annotated[int, Path(...)],
    db: Session = Depends(deps.get_db),
    target_id: Annotated[int | None, Body(...)] = -1,
    target_type: Annotated[str | None, Body()] = None,
    permissions: Annotated[dict[PermissionEnum, list[str | int]] | None, Body(...)] = None,
    current_user: models.User = Depends(deps.get_current_active_user),
    current_roles: list[models.Role] = Depends(deps.get_current_roles),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    if not deps.PermissionCheckId(target_type, PermissionEnum.modify)(
            target_id, db, current_user, current_roles
    ):
        raise HTTPException(403, f"You do not have permission to delete {target_type} {target_id}")

    # if we can create a file without a target type then we should be able to delete a file without one
    # if target_type is None:
    #     raise HTTPException(status_code=403, detail="Must provide target type and id")
    _removed_file = crud.file.remove_file(db, file_id=id, audit_logger=audit_logger)
    if not _removed_file:
        raise HTTPException(404, "File not found")

    return _removed_file


@router.post("/undelete", response_model=schemas.File)
def undelete_file(
    *,
    target_id: Annotated[int, Query(...)],
    keep_ids: Annotated[bool | None, Query(...)] = True,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    deleting_username = current_user.username
    if crud.permission.user_is_admin(db, current_user):
        deleting_username = None
    try:
        unremoved_file = crud.file.unremove_file(db, file_id=target_id, by_user=deleting_username, keep_ids=keep_ids, audit_logger=audit_logger)
        if not unremoved_file:
            raise HTTPException(404, "File not found")
        return unremoved_file
    except ValueError as e:
        raise HTTPException(422, str(e))
