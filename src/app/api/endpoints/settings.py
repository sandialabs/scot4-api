from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Body, Path
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.utils import create_schema_details
from app.auth import auth_classes
from app.object_storage import storage_provider_classes

router = APIRouter()


description, examples = create_schema_details(schemas.SettingsUpdate,
    "Change the global settings for this SCOT instance")


@router.put("/", summary="Update settings", response_model=schemas.Settings, description=description)
def update_setting(
    *,
    db: Session = Depends(deps.get_db),
    setting: Annotated[schemas.SettingsUpdate, Body(..., openapi_examples=examples)],
    _: models.User = Depends(deps.get_current_active_superuser),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
) -> schemas.Settings:
    """
    Update application settings
    """
    _setting = crud.setting.get(db)
    return crud.setting.update(db, db_obj=_setting, obj_in=setting, audit_logger=audit_logger)


@router.get("/", summary="Get settings", response_model=schemas.Settings)
def read_setting(
    *,
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_user),
) -> schemas.Settings:
    """
    Get current settings
    """
    # Don't audit log a simple settings pull
    return crud.setting.get(db)


# Auth method routes


@router.get("/auth", response_model=list[schemas.AuthSettings])
def read_auth_methods(
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_superuser),
) -> list[schemas.AuthSettings]:
    """
    Get all authentication methods currently configured for this SCOT instance
    """
    return crud.auth_setting.get_auth_methods(db)


description, _ = create_schema_details(schemas.AuthSettingsCreate)
auth_examples = {
    f"{auth_name.value}_basic": {
        "summary": f"{auth_name.value} auth template",
        "description": f"Shows configuration of a single {auth_name.value} auth instance",
        "value": {"auth": auth_name.value, "auth_properties": auth_classes[auth_name].config_help, "auth_active": True}
    } for auth_name in auth_classes
}


@router.post("/auth", response_model=schemas.AuthSettings, description=description)
def create_auth_method(
    new_settings: Annotated[schemas.AuthSettingsCreate, Body(..., openapi_examples=auth_examples)],
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_superuser),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
) -> schemas.AuthSettings:
    """
    Configure a new authentication method
    """
    return crud.auth_setting.create_auth_method(db, new_settings, audit_logger)


description, _ = create_schema_details(schemas.AuthSettingsUpdate)


@router.put("/auth/{id}", response_model=schemas.AuthSettings, description=description)
def update_auth_method(
    id: Annotated[int, Path(...)],
    settings: Annotated[schemas.AuthSettingsUpdate, Body(..., openapi_examples=auth_examples)],
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_superuser),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
) -> schemas.AuthSettings:
    """
    Update an existing authentication method
    """
    new_auth = crud.auth_setting.update_auth_method(db, id, settings, audit_logger)
    if new_auth:
        return new_auth
    else:
        raise HTTPException(404, f"Auth method with id {id} not found")


@router.delete("/auth/{id}", response_model=schemas.AuthSettings)
def delete_auth_method(
    id: Annotated[int, Path(...)],
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_superuser),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
) -> schemas.AuthSettings:
    """
    Delete an existing authentication method
    """
    try:
        old_auth = crud.auth_setting.remove_auth_method(db, id, audit_logger)
    except Exception as e:
        raise HTTPException(400, str(e))
    if old_auth:
        return old_auth
    else:
        raise HTTPException(404, f"Auth method with id {id} not found")


@router.get("/auth/help", response_model=schemas.AuthHelp)
def get_auth_help(
    _: models.User = Depends(deps.get_current_active_superuser),
) -> schemas.AuthHelp:
    """
    Retrieve information on the configuration parameters of each possible
    authentication method type
    """
    return crud.auth_setting.get_auth_help()


# Storage Provider Routes


@router.get("/storage_provider", response_model=list[schemas.StorageProviderSettings])
def read_storage_providers(
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_superuser),
) -> list[schemas.StorageProviderSettings]:
    return crud.storage_setting.get_multi(db)


@router.get("/storage_provider/{id}", response_model=schemas.StorageProviderSettings)
def read_storage_provider(
    id: Annotated[int, Path(...)],
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_superuser),
) -> schemas.StorageProviderSettings:
    """
    Get all storage providers currently configured for this SCOT instance
    """
    storage_provider = crud.storage_setting.get(db, id)

    if storage_provider:
        return storage_provider
    else:
        raise HTTPException(404, f"Storage provider with id {id} not found")


description, _ = create_schema_details(schemas.StorageProviderSettingsCreate)
storage_examples = {
    f"{storage_name.value}_basic": {
        "summary": f"{storage_name.value} storage provider template",
        "description": f"Shows configuration of a single {storage_name.value} storage provider instance",
        "value": {"provider": storage_name.value, "config": storage_provider_classes[storage_name].config_help, "enabled": True}
    } for storage_name in storage_provider_classes
}


@router.post("/storage_provider", response_model=schemas.StorageProviderSettings, description=description)
def create_storage_provider(
    new_settings: Annotated[schemas.StorageProviderSettingsCreate, Body(..., openapi_examples=storage_examples)],
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_superuser),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
) -> schemas.StorageProviderSettings:
    """
    Configure a new storage provider
    """
    return crud.storage_setting.create(db, new_settings, audit_logger)


description, _ = create_schema_details(schemas.StorageProviderSettingsUpdate)


@router.put("/storage_provider/{id}", response_model=schemas.StorageProviderSettings, description=description)
def update_storage_provider(
    id: Annotated[int, Path(...)],
    storage_provider: Annotated[schemas.StorageProviderSettingsUpdate, Body(..., openapi_examples=storage_examples)],
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_superuser),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
) -> schemas.StorageProviderSettings:
    """
    Update an existing storage provider
    """
    new_storage_provider = crud.storage_setting.update(db, id, storage_provider, audit_logger)
    if new_storage_provider:
        return new_storage_provider
    else:
        raise HTTPException(404, f"Storage provider with id {id} not found")


@router.delete("/storage_provider/{id}", response_model=schemas.StorageProviderSettings)
def delete_storage_provider(
    id: Annotated[int, Path(...)],
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_superuser),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
) -> schemas.StorageProviderSettings:
    """
    Delete an existing storage provider
    """
    old_storage_provider = crud.storage_setting.get(db, id)

    if not old_storage_provider:
        raise HTTPException(404, "Storage Provider not found")

    try:
        return crud.storage_setting.remove(db, _id=id, audit_logger=audit_logger)
    except Exception as e:
        raise HTTPException(400, str(e))


@router.get("/storage_provider_help", response_model=schemas.StorageProviderHelp)
def get_storage_provider_help(
    _: models.User = Depends(deps.get_current_active_superuser),
) -> schemas.StorageProviderHelp:
    """
    Retrieve information about the configuration parameters of each possible
    storage provider type
    """
    return crud.storage_setting.get_storage_provider_help()
