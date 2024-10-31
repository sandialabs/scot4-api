from datetime import datetime
from typing import Any, Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.utils import filter_fixup

router = APIRouter()


@router.get(
    "/{id}", response_model=schemas.Audit, dependencies=[Depends(deps.admin_only)]
)
def read_audit(
    *,
    db: Session = Depends(deps.get_db),
    id: Annotated[int, Path(...)],
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get audit by ID
    """
    _audit = crud.audit.get(db_session=db, _id=id)
    if not _audit:
        raise HTTPException(404, "Audit not found")

    return _audit


@router.get(
    "/", response_model=schemas.ListResponse[schemas.Audit], summary="Search audits"
)
def search_audits(
    *,
    db: Session = Depends(deps.get_db),
    skip: Annotated[int | None, Query(...)] = 0,
    limit: Annotated[int | None, Query(...)] = 100,
    sort: Annotated[str | None, Query(...)] = None,
    search_schema: schemas.AuditSearch = Depends(),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    ### Search using the available fields with the optional filters:
    - `!` - return the opposite result
    - `(n, n1)` - select values within the given range
    - `!(n, n1)` - select values **NOT** within the given range
    - `[n, n1, n2, ...]` - select multiple values with a list
    - `![n, n1, n2, ...]` - select multiple values **NOT** with a list
    - `\\` - use backslash to escape a special character

    ### Examples:
    - `id=!1` - return all ids that don't match the value
    - `modified=('2024-01-01', '2024-01-02)` - return all values between the dates
    - `modified=!('2024-01-01', '2024-01-02)` - return all values that are not between the dates
    - `created=['2024-01-01', '2024-01-02', '2024-01-04']` - return all values that have any of the created dates
    - `created=!['2024-01-01', '2024-01-02', '2024-01-04']` - return all values that don't have any of the created dates

    ### Note:
    Some fields can't use the range filters, for example `subject` or `description`. If range filters are provided the system will treat them as a list filter instead.
    """

    filter_dict = {
        "not": {}
    }
    key: str
    value: str
    for key, value in search_schema.model_dump().items():
        if value is None:
            continue

        try:
            # remove any extra whitespace
            value = value.strip()
            # check for escapes and if str?
            # !(n, n1) - not in range
            if value.startswith("!(") and value.endswith(")"):
                v0, v1 = value[2:-1].split(",")
                filter_dict["not"][key] = (search_schema.type_mapping(key, filter_fixup(v0)), search_schema.type_mapping(key, filter_fixup(v1)))
            # (n, n1) - range between two items i.e. ids, datetimes
            elif value.startswith("(") and value.endswith(")"):
                v0, v1 = value[1:-1].split(",")
                filter_dict[key] = (search_schema.type_mapping(key, filter_fixup(v0)), search_schema.type_mapping(key, filter_fixup(v1)))
            # ![n, n1, n2, ...] - not in list of items
            elif value.startswith("![") and value.endswith("]"):
                v = value[2:-1].split(",")
                filter_dict["not"][key] = [search_schema.type_mapping(key, filter_fixup(a)) for a in v]
            # [n, n1, n2, ...] - list of items
            elif value.startswith("[") and value.endswith("]"):
                v = value[1:-1].split(",")
                filter_dict[key] = [search_schema.type_mapping(key, filter_fixup(a)) for a in v]
            # !n - not an item
            elif value.startswith("!"):
                filter_dict["not"][key] = search_schema.type_mapping(key, filter_fixup(value[1:]))
            else:
                # remove any escape characters
                filter_dict[key] = search_schema.type_mapping(key, filter_fixup(value))
        except ValueError as e:
            raise HTTPException(422, str(e))

    # Users can only search their own audits if not admin
    if not crud.permission.user_is_admin(db, current_user):
        filter_dict["username"] = current_user.username

    _result, _count = crud.audit.query_with_filters(
        db,
        None,
        filter_dict,
        sort,
        skip,
        limit
    )
    return {"totalCount": _count, "resultCount": len(_result), "result": _result}


@router.delete(
    "/{id}", response_model=schemas.Audit, dependencies=[Depends(deps.admin_only)]
)
def delete_audit(
    id: Annotated[int, Path(...)],
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Delete an audit entry
    """
    _audit = crud.audit.remove(db_session=db, _id=id)
    if not _audit:
        raise HTTPException(404, "Audit not found")
    return _audit


# TODO: audits in other endpoint paths (e.g. /entity/{id}/audit)
