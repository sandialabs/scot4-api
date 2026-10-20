from fastmcp import FastMCP
from fastmcp.utilities.types import Image, File
from fastmcp.server.auth import MultiAuth
from fastmcp.server.auth.providers.azure import AzureProvider
from fastmcp.server.auth.providers.jwt import JWTVerifier
from fastmcp.server.auth.providers.debug import DebugTokenVerifier
from fastmcp.server.dependencies import get_access_token, get_http_request
from fastmcp.dependencies import Depends
from fastmcp.exceptions import ToolError, ResourceError
from contextlib import asynccontextmanager
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.exc import NoInspectionAvailable
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import NO_VALUE
from fastapi.encoders import jsonable_encoder
from key_value.aio.stores.base import BaseStore
from key_value.aio._utils.managed_entry import ManagedEntry
from key_value.aio.wrappers.encryption import FernetEncryptionWrapper
from cryptography.fernet import Fernet
import meilisearch

import base64
import logging
import json
import os
import hashlib
from datetime import datetime
from urllib.parse import quote
from typing import Annotated, Literal
from pydantic import Field

from app.core.config import settings
from app.core import security
from app.crud.crud_auth_setting import auth_setting
from app.crud.crud_user import user as crud_user
from app.crud.crud_apikey import apikey
from app import crud
from app.schemas import SearchRequest, SearchTypeMapping
from app.models import Role, User
from app.db.session import SessionLocal
from app.enums import AuthTypeEnum, EntryClassEnum, TargetTypeEnum, PermissionEnum
from app.crud.base import CRUDBase
from app.api import deps
from app.auth import get_authenticator
from app.utils import get_search_filters


@asynccontextmanager
async def get_db():
    with SessionLocal() as db_session:
        request = get_http_request()
        if request:
            request.state.db = db_session
        yield db_session


un_email_usernames = False


async def get_user(db: Session = Depends(get_db)):
    request = get_http_request()
    token = get_access_token()
    if not token:
        raise ToolError("Not authenticated")
    username = getattr(request.state, "user", None)
    if not username:
        username = token.claims.get("preferred_username")
    if username and "@" in username and un_email_usernames:
        username = username.split("@")[0]
    elif not username:
        username = token.claims.get("u")
    if username:
        user = crud_user.get_by_username(db, username=username)
        if crud_user.is_active(user):
            return user
        return None
    return None


async def get_roles(user: User = Depends(get_user)):
    token = get_access_token()
    if user is None:
        raise ToolError("Not authenticated")

    token_roles = None
    request = get_http_request()
    if request:
        token_roles = getattr(request.state, "token_roles", None)
    if token_roles is None and token:
        token_roles = token.claims.get("token_roles")
    if token_roles:
        return [role for role in user.roles if role.name in token_roles]
    return user.roles


class DBAuthStorage(BaseStore):
    STORAGE_KEY = "_MCP_STORAGE_"

    def __init__(self, auth_method_id, **kwargs):
        self.auth_method_id = auth_method_id
        super().__init__(stable_api=True, **kwargs)

    def _get_db(self):
        request = get_http_request()
        if request and hasattr(request.state, "db"):
            return request.state.db
        else:
            return SessionLocal()

    def _close_db(self, db):
        request = get_http_request()
        if not (request and hasattr(request.state, "db") and db == request.state.db):
            db.close()

    def _cull_collection(self, collection_obj):
        remove_keys = []
        for key, value in collection_obj.items():
            expiry = value.get("expires_at", "1970-01-01T00:00:00")
            if isinstance(expiry, str) and expiry < datetime.now().isoformat():
                remove_keys.append(key)
        for key in remove_keys:
            del collection_obj[key]
        return collection_obj

    async def _get_managed_entry(self, *, key: str, collection: str):
        db = self._get_db()
        settings = auth_setting.get(db, self.auth_method_id)
        if not settings:
            self._close_db(db)
            raise ValueError("Couldn't get authentication settings in storage")
        auth = get_authenticator(settings)
        collection_obj = json.loads(auth.storage.get(self.STORAGE_KEY + collection, "{}"))
        obj = collection_obj.get(key)
        result = None
        if obj:
            result = ManagedEntry(
                value=obj["value"],
                created_at=datetime.fromisoformat(obj["created_at"]) if obj["created_at"] else None,
                expires_at=datetime.fromisoformat(obj["expires_at"]) if obj["expires_at"] else None
            )
        self._close_db(db)
        return result

    async def _put_managed_entry(self, *, key: str, collection: str, managed_entry: ManagedEntry):
        db = self._get_db()
        settings = auth_setting.get(db, self.auth_method_id)
        if not settings:
            self._close_db(db)
            raise ValueError("Couldn't get authentication settings in storage")
        auth = get_authenticator(settings)
        collection_obj = json.loads(auth.storage.get(self.STORAGE_KEY + collection, "{}"))
        collection_obj[key] = {
            "value": managed_entry.value,
            "created_at": managed_entry.created_at_isoformat,
            "expires_at": managed_entry.expires_at_isoformat
        }
        self._cull_collection(collection_obj)
        auth.storage[self.STORAGE_KEY + collection] = json.dumps(collection_obj)
        db.commit()
        self._close_db(db)

    async def _delete_managed_entry(self, *, key: str, collection: str):
        db = self._get_db()
        settings = auth_setting.get(db, self.auth_method_id)
        if not settings:
            self._close_db(db)
            raise ValueError("Couldn't get authentication settings in storage")
        auth = get_authenticator(settings)
        collection_obj = json.loads(auth.storage.get(self.STORAGE_KEY + collection, "{}"))
        result = False
        if collection_obj and key in collection_obj:
            del collection_obj[key]
            result = True
        self._cull_collection(collection_obj)
        auth.storage[self.STORAGE_KEY + collection] = json.dumps(collection_obj)
        db.commit()
        self._close_db(db)
        return result


def validate_api_key(token: str):
    request = get_http_request()
    db = SessionLocal()
    try:
        keydata = apikey.get(db, token)
        if keydata is not None and keydata.active:
            request.state.user = keydata.owner
            request.state.token_roles = [role.name for role in keydata.roles] if keydata.roles else None
            return True
        return False
    finally:
        db.close()


def generate_single_list_or_range(name: str, value: str | list | tuple):
    if isinstance(value, list):
        return f"{name} IN {str(value)}"
    elif isinstance(value, tuple):
        return f"{name} >= {value[0]} AND {name} <= {value[1]}"
    elif isinstance(value, str):
        escaped_value = value.replace("'", "\\'")
        return f"{name} = '{escaped_value}'"
    else:
        return f"{name} = '{value}'"


def build_meilisearch_filter(search_body: SearchRequest) -> list[str]:
    search_dict = get_search_filters(
        search_body,
        ignore_fields=["limit", "offset", "crop_length", "sort"],
    )
    search_filter = []
    for key in search_dict:
        if key not in ["text", "not"]:
            search_filter.append(generate_single_list_or_range(key, search_dict[key]))
    for key in search_dict.get("not", []):
        if key != "text":
            search_filter.append("NOT (" + generate_single_list_or_range(key, search_dict["not"][key]) + ")")
    return search_filter


def build_meilisearch_sort(sort: str | list[str] | None) -> list[str]:
    sortable = [
        "entry_id",
        "target_type",
        "target_id",
        "created",
        "modified",
        "owner",
        "popularity_count",
    ]
    sort_order = []
    if sort is None:
        return sort_order
    if not isinstance(sort, list):
        sort = [sort]
    for sort_field in sort:
        if sort_field in sortable:
            sort_order.append(sort_field + ":asc")
        elif isinstance(sort_field, str) and sort_field.startswith("-") and sort_field[1:] in sortable:
            sort_order.append(sort_field[1:] + ":desc")
        elif isinstance(sort_field, str) and sort_field.startswith("+") and sort_field[1:] in sortable:
            sort_order.append(sort_field[1:] + ":asc")
        else:
            raise ToolError(f'"{sort_field}" is not a sortable search field')
    return sort_order


def format_search_hit(hit: dict) -> dict:
    formatted_hit = {
        key: value
        for key, value in hit.items()
        if key not in {"_formatted", "_matchesPosition"}
    }
    formatted_hit.update(hit.get("_formatted", {}))
    return formatted_hit


MCP_EXCLUDED_MODEL_FIELDS = {
    "favorite",
    "file_pointer",
    "popularity_voted",
    "subscribed",
    "message_id",
}


def get_loaded_relationship(obj, relationship_name: str):
    try:
        state = sa_inspect(obj)
    except NoInspectionAvailable:
        return None
    if relationship_name not in state.attrs:
        return None
    value = state.attrs[relationship_name].loaded_value
    if value is NO_VALUE:
        return None
    return value


def normalize_alert_cell_for_mcp(value):
    if isinstance(value, list) and len(value) == 1:
        return value[0]
    if isinstance(value, str):
        try:
            parsed_value = json.loads(value)
        except ValueError:
            return value
        if isinstance(parsed_value, list) and len(parsed_value) == 1:
            return parsed_value[0]
    return value


def normalize_alert_row_for_mcp(row: dict) -> dict:
    metadata_keys = {"id", "status", "promoted_ids"}
    return {
        key: value if key in metadata_keys else normalize_alert_cell_for_mcp(value)
        for key, value in row.items()
    }


def compact_model_for_mcp(obj, extra_fields: dict | None = None) -> dict | None:
    if obj is None:
        return None

    try:
        state = sa_inspect(obj)
    except NoInspectionAvailable:
        return obj

    result = {}
    for attr in state.mapper.column_attrs:
        if attr.key not in MCP_EXCLUDED_MODEL_FIELDS:
            result[attr.key] = getattr(obj, attr.key)

    tags = get_loaded_relationship(obj, "tags")
    if tags is not None:
        result["tags"] = [tag.name for tag in tags]

    sources = get_loaded_relationship(obj, "sources")
    if sources is not None:
        result["sources"] = [source.name for source in sources]

    entity_type = get_loaded_relationship(obj, "entity_type")
    if entity_type is not None:
        result["type_name"] = entity_type.name

    entity_classes = get_loaded_relationship(obj, "classes")
    if entity_classes is not None:
        result["classes"] = [entity_class.name for entity_class in entity_classes]

    data_cells = get_loaded_relationship(obj, "data_cells")
    if data_cells is not None and hasattr(obj, "data"):
        result["data"] = normalize_alert_row_for_mcp(dict(obj.data))

    alert_schema = get_loaded_relationship(obj, "alert_schema")
    if alert_schema is not None and hasattr(obj, "column_names"):
        result["columns"] = list(obj.column_names)

    if state.mapper.class_.__name__ == "AlertGroup":
        result["alerts"] = [
            normalize_alert_row_for_mcp(alert) for alert in obj.full_alert_data
        ]
        result["associated_sig_guide_map"] = obj.associated_sig_guide_map

    if extra_fields:
        result.update(extra_fields)
    return result


def compact_models_for_mcp(objs: list) -> list[dict | None]:
    return [compact_model_for_mcp(obj) for obj in objs]


def compact_entry_data_for_mcp(entry, entry_type: Literal["plain", "flaired", "all"]):
    if entry_type == "plain":
        if entry.entry_data and "plain_text" in entry.entry_data:
            return {"plain_text": entry.entry_data["plain_text"]}
        return {}
    if entry_type == "flaired":
        if entry.entry_data and "flaired_html" in entry.entry_data:
            return {"flaired_html": entry.entry_data["flaired_html"]}
        return {}
    return entry.entry_data


def compact_entry_for_mcp(entry, entry_type: Literal["plain", "flaired", "all"]):
    return compact_model_for_mcp(
        entry,
        {"entry_data": compact_entry_data_for_mcp(entry, entry_type)},
    )


def compact_alert_row_for_mcp(alert) -> dict:
    return normalize_alert_row_for_mcp({
        "id": alert.id,
        "status": alert.status,
        "promoted_ids": [promotion.p1_id for promotion in alert.promoted_to_targets],
        **dict(alert.data),
    })


def can_read_promotion_source(
    db: Session,
    source_type: TargetTypeEnum,
    source_id: int,
    user: User,
    roles: list[Role],
) -> bool:
    if source_type == TargetTypeEnum.alert:
        # Alerts inherit permissions from their containing alertgroup.
        alert = crud.alert.get(db, source_id)
        if alert is None:
            return False
        source_type = TargetTypeEnum.alertgroup
        source_id = alert.alertgroup_id

    source_roles = None
    if source_type not in deps.PermissionCheck.type_allow_whitelist:
        source_roles = roles
    try:
        deps.PermissionCheckId(source_type, PermissionEnum.read)(
            source_id,
            db,
            user,
            source_roles,
        )
        return True
    except Exception:
        return False


def get_promotion_source_entries(
    db: Session,
    source_type: TargetTypeEnum,
    source_id: int,
    roles: list[Role],
    entry_type: Literal["plain", "flaired", "all"],
) -> list[dict | None]:
    source_roles = None
    if source_type not in deps.PermissionCheck.type_allow_whitelist:
        source_roles = roles

    filter_dict = {
        "target_id": source_id,
        "target_type": source_type,
        "entry_class": EntryClassEnum.summary,
    }
    source_entries, count = crud.entry.query_with_filters(
        db,
        roles=source_roles,
        filter_dict=filter_dict,
        limit=None,
    )
    if count == 0:
        source_entries, _count = crud.entry.get_by_type(
            db,
            roles=source_roles,
            _id=source_id,
            _type=source_type,
            limit=None,
        )
    return [compact_entry_for_mcp(entry, entry_type) for entry in source_entries]


def add_promotion_source_content(
    db: Session,
    entry_data,
    entry_type: Literal["plain", "flaired", "all"],
    user: User,
    roles: list[Role],
):
    if not isinstance(entry_data, dict):
        return entry_data
    promotion_sources = entry_data.get("promotion_sources")
    if not isinstance(promotion_sources, list):
        return entry_data

    enriched_entry_data = dict(entry_data)
    enriched_sources = []
    for source in promotion_sources:
        if not isinstance(source, dict):
            enriched_sources.append(source)
            continue

        enriched_source = dict(source)
        source_type = TargetTypeEnum(source.get("type"))
        source_id = source.get("id")
        if source_type == TargetTypeEnum.none or source_id is None:
            enriched_sources.append(enriched_source)
            continue
        try:
            source_id = int(source_id)
        except (TypeError, ValueError):
            enriched_sources.append(enriched_source)
            continue

        if not can_read_promotion_source(db, source_type, source_id, user, roles):
            enriched_sources.append(enriched_source)
            continue

        if source_type == TargetTypeEnum.alert:
            alert = crud.alert.get(db, source_id)
            if alert is not None:
                enriched_source.update(compact_alert_row_for_mcp(alert))
        elif source_type == TargetTypeEnum.alertgroup:
            alertgroup = crud.alert_group.get(db, source_id)
            if alertgroup is not None:
                enriched_source["alerts"] = [
                    normalize_alert_row_for_mcp(alert)
                    for alert in alertgroup.full_alert_data
                ]
        else:
            enriched_source["entries"] = get_promotion_source_entries(
                db,
                source_type,
                source_id,
                roles,
                entry_type,
            )
        enriched_sources.append(enriched_source)

    enriched_entry_data["promotion_sources"] = enriched_sources
    return enriched_entry_data


def filter_search_results(db: Session, hits: list[dict], roles: list) -> list[dict]:
    all_hits = {}
    permission_pairs = {}
    for hit in hits:
        target_key = f"{hit['target_type']}-{hit['target_id']}"
        all_hits.setdefault(target_key, []).append(hit)
        permission_pairs[target_key] = {
            "id": hit["target_id"],
            "type": hit["target_type"],
        }
        if hit["target_type"] != TargetTypeEnum.alertgroup.value:
            permission_pairs[f"{TargetTypeEnum.entry.value}-{hit['entry_id']}"] = {
                "id": hit["entry_id"],
                "type": TargetTypeEnum.entry.value,
            }

    filter_list = crud.permission.filter_search_hits(db, list(permission_pairs.values()), roles)
    if filter_list is False:
        filtered_results = []
        for grouped_hits in all_hits.values():
            filtered_results.extend([format_search_hit(hit) for hit in grouped_hits])
        return filtered_results

    readable_targets = {f"{target_type.value}-{target_id}" for target_type, target_id in filter_list}
    filtered_results = []
    for target_key, grouped_hits in all_hits.items():
        if target_key in readable_targets:
            for hit in grouped_hits:
                if hit["target_type"] == TargetTypeEnum.alertgroup.value:
                    filtered_results.append(format_search_hit(hit))
                elif f"{TargetTypeEnum.entry.value}-{hit['entry_id']}" in readable_targets:
                    filtered_results.append(format_search_hit(hit))
    return filtered_results


def create_mcp_server(base_app):
    providers = auth_setting.get_auth_methods(SessionLocal())
    azure_settings = None
    provider_id = None
    client_storage = None
    for provider in providers:
        if provider.auth_active and provider.auth == AuthTypeEnum.aad:
            azure_settings = provider.auth_properties
            provider_id = provider.id
    if azure_settings:
        _, authority, tenant_id = azure_settings["authority"].rsplit("/", 2)
        global un_email_usernames
        un_email_usernames = azure_settings["un_email_usernames"]
        secret_key = None
        try:
            secret_key = settings.MCP_OAUTH_SECRET_KEY
            if secret_key and len(base64.b64decode(secret_key)) != 32:
                secret_key = hashlib.sha256(secret_key.encode('latin1')).digest()
                secret_key = base64.b64encode(secret_key)
        except Exception as e:
            secret_key = None
        if secret_key:
            client_storage = FernetEncryptionWrapper(
                key_value=DBAuthStorage(provider_id),
                fernet=Fernet(secret_key)
            )
        else:
            logging.warning("MCP_OAUTH_SECRET_KEY not set, tokens will be stored in cleartext")
            client_storage = DBAuthStorage(provider_id)
        auth = MultiAuth(
            server=AzureProvider(
               client_id=azure_settings["client_id"],
               client_secret=azure_settings["client_secret"],
               tenant_id=tenant_id,
               required_scopes=["MCP"],
               additional_authorize_scopes=azure_settings["scopes"],
               base_authority=authority,
               base_url=settings.API_EXTERNAL_BASE.removesuffix(settings.API_V1_STR),
               jwt_signing_key=settings.SECRET_KEY,
               client_storage=client_storage
            ),
            verifiers=[
                JWTVerifier(
                    public_key=settings.SECRET_KEY,
                    algorithm=security.ALGORITHM,
                ),
                DebugTokenVerifier(
                    validate=validate_api_key,
                    client_id="apikey-client",
                    scopes=["MCP"]
                )
            ],
            required_scopes=[]
        )
    else:
        logging.warning("MCP oauth disabled because azure auth is not configured")
        auth = MultiAuth(
            verifiers=[
                JWTVerifier(
                    public_key=settings.SECRET_KEY,
                    algorithm=security.ALGORITHM,
                ),
                DebugTokenVerifier(
                    validate=validate_api_key,
                    client_id="apikey-client",
                    scopes=["MCP"]
                )
            ]
        )
    mcp = FastMCP(
        auth=auth,
        name="SCOT MCP Server",
        instructions="The Sandia Cyber Omni Tracker (SCOT) is a cyber security incident response management system and knowledge base.",
    )

    @mcp.tool
    def search(
        text: Annotated[str, Field(description="Words or phrase to search for across indexed SCOT text.")],
        limit: Annotated[int, Field(description="Maximum number of results to return.")] = 100,
        offset: Annotated[int, Field(description="Number of matching results to skip for pagination.")] = 0,
        crop_length: Annotated[int, Field(description="Approximate snippet length around matching text. Increase for more context.")] = 30,
        entry_id: Annotated[str | None, Field(description="Filter by entry id. Supports SCOT filter syntax.")] = None,
        created: Annotated[str | None, Field(description="Filter by created timestamp. Supports date ranges like `(2024-01-01, 2024-02-01)`.")] = None,
        modified: Annotated[str | None, Field(description="Filter by modified timestamp. Supports date ranges like `(2024-01-01, 2024-02-01)`.")] = None,
        sort: Annotated[str | list[str] | None, Field(description="Sort field or fields. Prefix with `-` for descending, for example `-modified`.")] = None,
        owner: Annotated[str | None, Field(description="Filter by owner username. Supports SCOT filter syntax.")] = None,
        target_type: Annotated[TargetTypeEnum | None, Field(description="Restrict results to one parent SCOT object type.")] = None,
        target_id: Annotated[str | None, Field(description="Filter by parent object id. Supports SCOT filter syntax.")] = None,
        popularity_count: Annotated[str | None, Field(description="Filter by popularity count. Supports numeric ranges like `(5, 20)`.")] = None,
        db: Session = Depends(get_db),
        user: User = Depends(get_user),
        roles: list[Role] = Depends(get_roles),
    ):
        """
        Perform a full-text search across SCOT entries, alerts, and object titles.

        Output:
        - `index_id`: starts with "a" for alert hits and "e" for entry hits.
        - `entry_text`: alert field data for alert hits, or a cropped plain-text entry snippet for entry hits.
        - `target_type` and `target_id`: the parent SCOT object for the hit.
        - `parent_text`: the parent object's title.

        Required parameter:
        - `text`: the words or phrase to search for.

        Paging and context:
        - `limit`: maximum results to return.
        - `offset`: number of matching results to skip.
        - `crop_length`: approximate snippet length around matching text. Increase it when the result needs more context.

        Optional filters:
        - `target_type`: restrict results to one SCOT object type when you know where relevant information should be.
        - `target_id`, `entry_id`, `owner`, `created`, `modified`, and `popularity_count`: filter by those indexed fields.

        Filter syntax:
        - `value` matches one value.
        - `!value` excludes one value.
        - `(start, end)` matches a numeric or date range.
        - `!(start, end)` excludes a numeric or date range.
        - `[a, b, c]` matches any listed value.
        - `![a, b, c]` excludes listed values.
        - Prefix a leading special character with `\\`, for example `\\!important`.

        Sorting:
        - `sort` accepts `entry_id`, `target_type`, `target_id`, `created`, `modified`, `owner`, or `popularity_count`.
        - Prefix with `-` for descending or `+` for explicit ascending, for example `-modified`.

        Results are permission-filtered. Alerts inherit permissions from their alertgroup; entry hits require read access to both the entry and its parent object.
        """
        if user is None:
            raise ToolError("Not authenticated")

        search_body = SearchRequest(
            text=text,
            limit=limit,
            offset=offset,
            crop_length=crop_length,
            entry_id=entry_id,
            created=created,
            modified=modified,
            sort=None,
            owner=owner,
            target_type=target_type.value if target_type else None,
            target_id=target_id,
            popularity_count=popularity_count,
        )
        try:
            search_filter = build_meilisearch_filter(search_body)
            sort_order = build_meilisearch_sort(sort)
        except ValueError as e:
            raise ToolError(str(e))

        client = meilisearch.Client(settings.SEARCH_HOST, settings.SEARCH_API_KEY)
        entries_index = client.index("entries")
        entries_hits = entries_index.search(
            search_body.text,
            {
                "cropLength": search_body.crop_length,
                "limit": search_body.limit,
                "offset": search_body.offset,
                "attributesToCrop": ["entry_text"],
                "filter": search_filter,
                "sort": sort_order,
            },
        )

        return jsonable_encoder(filter_search_results(db, entries_hits["hits"], roles))

    @mcp.resource(uri="resource://object/{object_type}/{object_id}", mime_type="text/markdown")
    def object_resource(
        object_type: TargetTypeEnum,
        object_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(get_user),
        current_roles: list[Role] = Depends(get_roles),
    ):
        """
        Retrieves a single SCOT object of the specified type by id,
        and provides it in markdown format
        """
        if object_type in deps.PermissionCheck.type_allow_whitelist:
            roles = None  # Don't check roles if an element does not have permissions (like entities, tags, sources, etc.)
        else:
            roles = current_roles
        try:
            deps.PermissionCheckId(object_type, PermissionEnum.read)(object_id, db, user, roles)
        except Exception as e:
            raise ResourceError(e.message)
        object_crud = CRUDBase.target_crud_mapping.get(object_type)
        obj = object_crud.get(db, object_id)
        tmp_file, media_type = export_object(db, obj, obj_type, "md", object_type.name.replace("_", " "), roles)
        content = open(tmp_file).read()
        os.remove(tmp_file)
        return content

    @mcp.tool
    def get_object(
        object_type: TargetTypeEnum,
        object_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(get_user),
        current_roles: list[Role] = Depends(get_roles),
    ):
        """
        Retrieves a single SCOT object of the specified type by id,
        along with the plain text of its entries (if any). Retrieve its entries
        instead to get the full HTML data of each entry.
        Object types are:
        alert - A row of columnar data that represents a single suspicious occurrence that may warrant future investigation
        alertgroup - A set of related alerts that triggered from the same signature
        dispatch - An unverified threat intelligence news article or post from an external source
        entity - A short string such as a name, domain, or IP address that can be cross-referenced across different SCOT objects
        event - An object documenting an active investigation by a member of the incident response team, often promoted from one or more alerts
        file - A file uploaded to SCOT, often attached to another object
        guide - A set of incident response instructions, often describing how to triage an alert triggered by a signature linked to the guide
        incident - An object documenting a reportable incident that is verified to have occurred, often promoted from an event
        intel - A curated threat intelligence item on a particular topic, sometimes promoted from one or more dispatches
        product - A report on a particular threat intelligence topic, often compiled from a number of intel items
        signature - An object representing a detection that can generate alerts that will be fed into SCOT
        entity_class - A characteristic common to one or more entities (e.g. country of origin)
        entity_type - Represents a particular type of entity (e.g. domain, ip address)
        source - A label that can be attached to any other object to document the source of its information
        tag - A label that can be attached to any other object representing a user-defined category associated with that object
        feed - Documents a particular recurring source of information
        pivot - An external URL template that represents a place to retrieve additional contextual information about an entity
        vuln_feed - A collection of information about a particular software vulnerability
        vuln_track - A curated set of information about a vulnerability and how the vulnerability team is tracking it, often promoted from a vuln_feed
        """
        if object_type in deps.PermissionCheck.type_allow_whitelist:
            roles = None  # Don't check roles if an element does not have permissions (like entities, tags, sources, etc.)
        else:
            roles = current_roles
        try:
            deps.PermissionCheckId(object_type, PermissionEnum.read)(object_id, db, user, roles)
        except Exception as e:
            raise ToolError(e.message)
        object_crud = CRUDBase.target_crud_mapping.get(object_type)
        obj = object_crud.get(db, object_id)
        plain_text_entries = []
        if obj:
            entries, _count = crud.entry.get_by_type(
                db, _type=object_type, _id=object_id, roles=roles
            )
            plain_text_entries = [
                entry.entry_data.get("plain_text")
                for entry in entries
                if entry.entry_data and entry.entry_data.get("plain_text")
            ]
        return jsonable_encoder(
            compact_model_for_mcp(obj, {"plain_text_entries": plain_text_entries})
        )

    @mcp.tool
    def search_objects(
        object_type: TargetTypeEnum,
        filters: dict,
        skip: int = 0,
        limit: int = 100,
        sort: str | None = None,
        db: Session = Depends(get_db),
        user: User = Depends(get_user),
        current_roles: list[Role] = Depends(get_roles),
    ):
        """
        ### Perform a paginated search, filtering on one or more available fields
        Each filter is an entry in the `filters` dictionary of the form: <field>: <filter>.
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
        | `modified=(2024-01-01, 2024-01-02)` | return all items last modified between the dates |
        | `modified=!(2024-01-01, 2024-01-02)` | return all items that were not last modified between the dates |
        | `owner=[alice, bob]` | return all items that have any of the listed owners |
        | `owner=![charlie, dave]` | return all items that don't have any of the listed owners |
        | `name=\\!test` | return all items with names that match including the `!`, but not including the `\\`|
        | `name=\\(test)` | return all items with names that match including the `(` and `)`, but not including the `\\` |

        ### Notes:
        - Non-numeric/non-date fields can't use the range filters, for example `subject` or `description`. If range filters are provided the system will treat them as a list filter instead.
        - If none of the range or list filters work it will attempt to do a normal search
        - Datetimes are in standard ISO format
        - To sort by a field, pass the field name to the `sort` parameter. Prefixing a dash (-) character will casue the field to sort in descending order instead of ascending.
        ### Possible filters:
        You can filter on all the below fields, plus any field that is returned from an object. Particular object types might have more fields, but do not make up new field names or search an object for a field it doesn't have.

        | Field Name | Description | Object Types |
        | id | object id | all |
        | created | object creation time | all |
        | modified | object last modified time | all |
        | owner | creator of object | alertgroup, event, incident, entry, dispatch, intel, product, guide, signature, vuln_feed, vuln_track |
        | subject | subject (title) of the object |alertgroup, event, incident, dispatch, intel, product, vuln_feed, vuln_track |
        | name | name of the object | signature, entity_class, source, tag |
        | entry_count | number of entries in the object | event, incident, dispatch, intel, product, guide, vuln_feed, vuln_track |
        | status | status of the object (open, closed, or promoted) | alert, event, incident, dispatch, intel, vuln_feed, vuln_track |
        | view_count | number of times the object has been viewed | alertgroup, event, incident, vuln_feed, vuln_track |
        """
        if object_type in deps.PermissionCheck.type_allow_whitelist:
            roles = None  # Don't check roles if an element does not have permissions (like entities, tags, sources, etc.)
        else:
            roles = current_roles
        try:
            search_obj = SearchTypeMapping[object_type](**filters)
            filter_dict = get_search_filters(search_obj)
            object_crud = CRUDBase.target_crud_mapping.get(object_type)
            _result, _count = object_crud.query_with_filters(db, roles, filter_dict, sort, skip, limit)
        except ValueError as e:
            raise ToolError(str(e))
        return jsonable_encoder(
            {
                "totalCount": _count,
                "resultCount": len(_result),
                "result": compact_models_for_mcp(_result),
            }
        )

    @mcp.tool
    def get_object_entries(
        object_type: TargetTypeEnum,
        object_id: int,
        skip: int = 0,
        limit: int = 100,
        entry_type: Literal["plain", "flaired", "all"] = "plain",
        db: Session = Depends(get_db),
        user: User = Depends(get_user),
        current_roles: list[Role] = Depends(get_roles),
    ):
        """
        Gets all of the paginated entry data for a SCOT object. An `entry_type` of "plain",
        returns only the plain-text entry data field, an `entry_type` of "flaired" returns
        only the flaired html (what the user usually sees, somewhat verbose), and an
        `entry_type` of "all" returns all data (very verbose and usually unnecessary; ONLY
        USE when you need information about visual entry layouts and links).
        """
        if object_type in deps.PermissionCheck.type_allow_whitelist:
            roles = None  # Don't check roles if an element does not have permissions (like entities, tags, sources, etc.)
        else:
            roles = current_roles
        try:
            deps.PermissionCheckId(object_type, PermissionEnum.read)(object_id, db, user, roles)
        except Exception as e:
            raise ToolError(e.message)
        _entries, count = crud.entry.get_by_type(
            db,
            roles=roles,
            _id=object_id,
            _type=object_type,
            skip=skip,
            limit=limit,
        )
        compact_entries = []
        for entry in _entries:
            if entry.entry_class == EntryClassEnum.promotion:
                entry_data = add_promotion_source_content(
                    db,
                    entry.entry_data,
                    entry_type,
                    user,
                    current_roles,
                )
            else:
                entry_data = compact_entry_data_for_mcp(entry, entry_type)
            compact_entries.append(
                compact_model_for_mcp(entry, {"entry_data": entry_data})
            )
        return jsonable_encoder(
            {
                "totalCount": count,
                "resultCount": len(_entries),
                "result": compact_entries,
            }
        )

    @mcp.tool
    def read_entities(
        object_type: TargetTypeEnum,
        object_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(get_user),
        roles: list[Role] = Depends(get_roles),
    ):
        """
        Get all of the entities (e.g. domains, ip addresses, hashes) associated with a SCOT object
        """
        deps.PermissionCheckId(object_type, PermissionEnum.read)(object_id, db, user, roles)
        _entities, count = crud.entity.retrieve_element_entities(db, object_id, object_type)
        return jsonable_encoder(
            {
                "totalCount": count,
                "resultCount": len(_entities),
                "result": compact_models_for_mcp(_entities),
            }
        )

    @mcp.tool
    def entity_pivot(
        entity_id: Annotated[int, Field(description="Entity id to pivot from.")],
        skip: Annotated[int, Field(description="Number of matching objects to skip per object type.")] = 0,
        limit: Annotated[int, Field(description="Maximum number of matching objects to return per object type.")] = 10,
        db: Session = Depends(get_db),
        user: User = Depends(get_user),
        roles: list[Role] = Depends(get_roles),
    ):
        """
        Find SCOT objects where an entity appears, grouped by object type.

        Use this after `read_entities` to pivot from a known SCOT object to
        other alerts, events, intel, products, incidents, dispatches,
        signatures, vuln feeds, or vuln tracks that share the selected entity.
        The pagination parameters apply to each object type individually.
        """
        try:
            deps.PermissionCheckId(TargetTypeEnum.entity, PermissionEnum.read)(
                entity_id,
                db,
                user,
                roles,
            )
        except Exception as e:
            raise ToolError(getattr(e, "message", str(e)))

        appearances = crud.entity.retrieve_entity_links_for_flair_pane(
            db,
            entity_id,
            skip,
            limit,
        )
        return jsonable_encoder(appearances)

    @mcp.tool
    def download_file(file_id: int, db: Session = Depends(get_db), user: User = Depends(get_user)):
        """
        Download a file from SCOT
        """
        fileobj = crud.file.get(db, file_id)
        if fileobj is None:
            raise ToolError(f"File {file_id} not found")
        try:
            filestream = crud.file.get_content(db, fileobj)
        except Exception as e:
            raise ToolError(f"Could not retrieve file {file_id} data from storage - {e}")

        filename = quote(fileobj.filename.encode("utf-8"))
        content = filestream.read()  # Set size limit?
        content_type = fileobj.content_type
        modified_content_type = fileobj.content_type
        if modified_content_type and "/" in modified_content_type:
            modified_content_type = modified_content_type.split("/", 1)[1]
        if not modified_content_type and filename and filename.endswith((".png", ".jpg", ".jpeg", ".gif")):
            filetype = filename.split(".")[-1]
            if filetype == "jpg":
                filetype = "jpeg"
            modified_content_type = filetype
            content_type = "image/" + filetype

        if content_type and content_type.startswith("image"):
            return Image(data=content, format=modified_content_type)
        else:
            return File(data=content, format=modified_content_type)

    mcp_app = mcp.http_app(path="/mcp")
    return mcp_app
