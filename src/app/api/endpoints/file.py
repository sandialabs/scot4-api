import hashlib
import time
import random
import string
import pyzipper
import os
from typing import Annotated
from urllib.parse import quote
from streaming_form_data import StreamingFormDataParser
from streaming_form_data.targets import SHA256Target
from fastapi import Request, APIRouter, Depends, HTTPException, Query, Body, Path
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
from starlette.background import BackgroundTask
from pydantic.json_schema import SkipJsonSchema

from app import crud, models, schemas
from app.api import deps
from app.enums import PermissionEnum, TargetTypeEnum
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


# Some generics
generic_get(router, crud.file, TargetTypeEnum.file, schemas.File)
generic_put(router, crud.file, TargetTypeEnum.file, schemas.File, schemas.FileUpdate)


@router.post("/", response_model=schemas.File, summary="Create a file")
async def create_file(
    *,
    db: Session = Depends(deps.get_db),
    request: Request,
    current_user: models.User = Depends(deps.get_current_active_user),
    current_roles: list[models.Role] = Depends(deps.get_current_roles),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    """
    Upload a file. The body of the request itself will become the content of
    the stored file. You can also provide the `target_type`, `target_id`, and
    `description` fields in the request headers. If target_type and target_id
    are provided, the file will be attached to the specified object (and have
    its same permissions)
    """
    nonce = "".join(random.choices(string.ascii_lowercase, k=30))  # nosec
    file_reference_id = hashlib.sha256(f"{current_user.username}:{time.time()}:{nonce}".encode('utf-8')).hexdigest()
    target_id = request.headers.get('target_id')
    target_type = request.headers.get('target_type')
    description = request.headers.get('description')
    if target_type is not None:
        target_type = target_type.lower()
    if target_id is not None and target_type is not None:
        if not deps.PermissionCheckId(target_type, PermissionEnum.modify)(target_id, db, current_user, current_roles):
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
            file_pointer=file_reference_id,
            description=description
        )
        if target_type is not None and target_id is not None:
            created_file_obj = crud.file.create_in_object(
                db,
                obj_in=obj_in,
                source_type=target_type,
                source_id=target_id,
                audit_logger=audit_logger
            )
        else:
            created_file_obj = crud.file.create(db, obj_in=obj_in, audit_logger=audit_logger)
        return created_file_obj
    except Exception as e:
        raise HTTPException(422, str(e))


def _download(db: Session, audit_logger: deps.AuditLogger, ids: list[int], password: str = None):
    zipfile = None
    if len(ids) > 1 or password is not None:
        try:
            zipfile = pyzipper.AESZipFile("scot_download.zip", "w", compression=pyzipper.ZIP_DEFLATED)
            if password is not None:
                zipfile.setencryption(pyzipper.WZ_AES)
                zipfile.setpassword(password.encode("utf-8"))
        except Exception as e:
            raise HTTPException(422, f"Failed to create zipfile {e}")

    for id in ids:
        fileobj = crud.file.get(db, id, audit_logger)
        if fileobj is None:
            raise HTTPException(404, f"File {id} not found")
        try:
            filestream = crud.file.get_content(db, fileobj)
        except Exception as e:
            raise HTTPException(500, f"Could not retrieve file {id} data from storage - {e}")

        # if only one file to download and no password was provided send the file
        if len(ids) == 1 and password is None:
            return StreamingResponse(
                filestream,
                media_type=fileobj.content_type,
                headers={
                    "content-disposition": f"attachment; filename*=UTF-8''{quote(fileobj.filename.encode('utf-8'))}"
                },
            )
        # otherwise add file to zip
        elif zipfile is not None:
            try:
                zipfile.writestr(fileobj.filename, filestream.read())
            except Exception as e:
                raise HTTPException(500, f"Could not add file {id} to zip - {e}")

    zipfile.close()

    return FileResponse(
        "scot_download.zip",
        filename="scot_download.zip",
        background=BackgroundTask(os.remove, "scot_download.zip")
    )


# Generics
generic_tag_untag(router, crud.file, TargetTypeEnum.file, schemas.File)
generic_source_add_remove(router, crud.file, TargetTypeEnum.file, schemas.File)
generic_history(router, crud.file, TargetTypeEnum.file)
generic_search(router, crud.file, TargetTypeEnum.file, schemas.FileSearch, schemas.File)


@router.get("/download/many", summary="Download many files", description="Download zip of all files and optionally encrypt the download with a provided password.")
def download_files(
    ids: Annotated[list[int], Query(description="A list of file ids to download, a zip of all file will be created.")],
    password: Annotated[str | SkipJsonSchema[None], Query(description="A password to use to create an encrypted zip file")] = None,
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_user),
    current_roles: list[models.Role] = Depends(deps.get_current_roles),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    return _download(db, audit_logger, ids, password)


@router.get("/download/{id}", summary="Download a file", description="Download a file and optionally encrypt the file with a provided password.")
def download_file(
    id: Annotated[int, Path(description="A file id to download")],
    password: Annotated[str | SkipJsonSchema[None], Query(description="A password to use to create an encrypted zip file")] = None,
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_user),
    current_roles: list[models.Role] = Depends(deps.get_current_roles),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    return _download(db, audit_logger, [id], password)


@router.delete("/many", response_model=list[schemas.File], dependencies=[Depends(deps.PermissionCheckIds(TargetTypeEnum.file, PermissionEnum.delete))])
def delete_files(
    *,
    ids: Annotated[list[int], Query(...)],
    db: Session = Depends(deps.get_db),
    target_id: Annotated[int | None, Body(...)] = -1,
    target_type: Annotated[str | None, Body()] = None,
    current_user: models.User = Depends(deps.get_current_active_user),
    current_roles: list[models.Role] = Depends(deps.get_current_roles),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    _obj = []
    for id in ids:
        _obj.append(delete_file(id=id, db=db, target_id=target_id, target_type=target_type, current_user=current_user, current_roles=current_roles, audit_logger=audit_logger))
    return _obj


@router.delete("/{id}", response_model=schemas.File, dependencies=[Depends(deps.PermissionCheckId(TargetTypeEnum.file, PermissionEnum.delete))])
def delete_file(
    *,
    id: Annotated[int, Path(...)],
    db: Session = Depends(deps.get_db),
    target_id: Annotated[int, Body(..., examples=[0])] = -1,
    target_type: Annotated[str | SkipJsonSchema[None], Body()] = None,
    current_user: models.User = Depends(deps.get_current_active_user),
    current_roles: list[models.Role] = Depends(deps.get_current_roles),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    if not deps.PermissionCheckId(target_type, PermissionEnum.modify)(target_id, db, current_user, current_roles):
        raise HTTPException(403, f"You do not have permission to delete {target_type} {target_id}")

    _removed_file = crud.file.remove_file(db, id, audit_logger)
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
        unremoved_file = crud.file.unremove_file(db, target_id, deleting_username, keep_ids, audit_logger)
        if not unremoved_file:
            raise HTTPException(404, "File not found")
        return unremoved_file
    except ValueError as e:
        raise HTTPException(422, str(e))
