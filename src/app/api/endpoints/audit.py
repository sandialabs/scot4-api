from typing import Any, Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from pydantic.json_schema import SkipJsonSchema

from app import crud, models, schemas
from app.api import deps
from app.utils import get_search_filters

router = APIRouter()


@router.get(
    "/{id}",
    response_model=schemas.Audit,
    summary="Get an audit",
    dependencies=[Depends(deps.admin_only)]
)
def read_audit(
    *,
    db: Session = Depends(deps.get_db),
    id: Annotated[int, Path(...)],
    _: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get an audit entry by ID
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
    skip: Annotated[int, Query(...)] = 0,
    limit: Annotated[int, Query(...)] = 100,
    sort: Annotated[str | SkipJsonSchema[None], Query(...)] = None,
    search_schema: schemas.AuditSearch = Depends(),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    ### Perform a paginated search, optionally filtering on one or more available fields.
    Only results that match all filters will be returned. The filters can be modified
    using the syntax below.
    | | |
    | --- | --- |
    | `!` | return the opposite result |
    | `(n, n1)` | select values within the given range |
    | `!(n, n1)` | select values **NOT** within the given range |
    | `[n, n1, n2, ...]` | select multiple values within a list |
    | `![n, n1, n2, ...]` | select **NOT** multiple values within a list |
    | `\\` | use a backslash to escape a special character at the beginning of your search string; you must escape a starting parenthesis `(`, bracket `[`, or exclamation point `!` or it will be interpreted as above |

    ### Examples:
    | | |
    | --- | --- |
    | `id=1` | return all items with ids that match the value |
    | `id=!1` | return all items with ids that don't match the value |
    | `when_date=(2024-01-01, 2024-01-02)` | return all items created between the dates |
    | `when_date=!(2024-01-01, 2024-01-02)` | return all items that were not created between the dates |
    | `username=[alice, bob]` | return all items that have any of the listed users |
    | `username=![charlie, dave]` | return all items that don't have any of the listed users |
    | `username=\\!test` | return all items with names that match including the `!`, but not including the `\\`|
    | `username=\\(test)` | return all items with names that match including the `(` and `)`, but not including the `\\` |

    ### Notes:
    - Non-numeric/non-date fields can't use the range filters, for example `subject` or `description`. If range filters are provided the system will treat them as a list filter instead.
    - If none of the range or list filters work it will attempt to do a normal search
    - Datetimes are parsed using the [dateutil module](https://dateutil.readthedocs.io/en/stable/parser.html#dateutil.parser.parse)
        - Some fields (e.g. event subjects and entity values) default to "contains" string searches, where any item containing the searched string will match (so searching for `example.com` would match both `example.com` and `foo.example.com`). Searching these fields with list searches (with square brackets) disables this feature for all list items, but "range" searches (with parentheses) search normally. For example, searching `[example.com]` wouldn't match `foo.example.com` but searching `(example.com)` would match.
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
    summary="Delete an audit",
    dependencies=[Depends(deps.admin_only)]
)
def delete_audit(
    id: Annotated[int, Path(...)],
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Delete an audit entry by ID
    """
    _audit = crud.audit.remove(db, _id=id)
    if not _audit:
        raise HTTPException(404, "Audit not found")
    return _audit


# TODO: audits in other endpoint paths (e.g. /entity/{id}/audit)
