from typing import Any, Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.utils import get_search_filters

router = APIRouter()


@router.get(
    "/{id}",
    response_model=schemas.Audit,
    dependencies=[Depends(deps.admin_only)]
)
def read_audit(
    *,
    db: Session = Depends(deps.get_db),
    id: Annotated[int, Path(...)],
    _: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get audit by ID
    """
    _audit = crud.audit.get(db, id)
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
    | | |
    | --- | --- |
    | `!` | return the opposite result |
    | `(n, n1)` | select values within the given range |
    | `!(n, n1)` | select values **NOT** within the given range |
    | `[n, n1, n2, ...]` | select multiple values within a list |
    | `![n, n1, n2, ...]` | select multiple values **NOT** within a list |
    | `\\` | use backslash to escape a special character please note that you must escape the starting parentheses `(` or the bracket `[` |

    ### Examples:
    | | |
    | --- | --- |
    | `id=!1` | return all ids that don't match the value |
    | `modified=('2024-01-01', '2024-01-02')` | return all values between the dates |
    | `modified=!('2024-01-01', '2024-01-02')` | return all values that are not between the dates |
    | `created=['2024-01-01', '2024-01-02', '2024-01-04']` | return all values that have any of the created dates |
    | `created=!['2024-01-01', '2024-01-02', '2024-01-04']` | return all values that don't have any of the created dates |
    | `name=\\!test` | return all names that match including the `!` |
    | `name=\\(test)` | return all names that match including the `(` and `)` |

    ### Notes:
    - Some fields can't use  the range filters, for example `subject` or `description`. If range filters are provided the system will treat them as a list filter instead.
    - If none of the range or list filters work it will attempt to do a normal search
    - Datetimes are parsed using the [dateutil module](https://dateutil.readthedocs.io/en/stable/parser.html#dateutil.parser.parse)
    """

    try:
        filter_dict = get_search_filters(search_schema)
        # Users can only search their own audits if not admin
        if not crud.permission.user_is_admin(db, current_user):
            filter_dict["username"] = current_user.username
        _result, _count = crud.audit.query_with_filters(db, None, filter_dict, sort, skip, limit)            
    except ValueError as e:
        raise HTTPException(422, str(e))

    return {"totalCount": _count, "resultCount": len(_result), "result": _result}


@router.delete(
    "/{id}",
    response_model=schemas.Audit,
    dependencies=[Depends(deps.admin_only)]
)
def delete_audit(
    id: Annotated[int, Path(...)],
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Delete an audit entry
    """
    _audit = crud.audit.remove(db, _id=id)
    if not _audit:
        raise HTTPException(404, "Audit not found")
    return _audit


# TODO: audits in other endpoint paths (e.g. /entity/{id}/audit)
