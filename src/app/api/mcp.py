from fastmcp import FastMCP
from fastmcp.server.providers.openapi import OpenAPIProvider, RouteMap, MCPType, OpenAPITool, OpenAPIResource
from fastmcp.tools import Tool
from fastmcp.tools.tool_transform import forward
from fastmcp.utilities.types import Image, File
from fastmcp.server.auth import MultiAuth
from fastmcp.server.auth.providers.azure import AzureProvider
from fastmcp.server.auth.providers.jwt import JWTVerifier
from fastmcp.server.auth.providers.debug import DebugTokenVerifier
from fastmcp.server.dependencies import get_access_token, get_http_request
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.dependencies import Depends
from fastmcp.exceptions import ToolError, ResourceError
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from key_value.aio.stores.base import BaseStore
from key_value.aio._utils.managed_entry import ManagedEntry
from key_value.aio.wrappers.encryption import FernetEncryptionWrapper
from cryptography.fernet import Fernet
import httpx

import asyncio
import base64
import logging
import json
import os
import hashlib
from datetime import datetime, timedelta
from urllib.parse import quote
from typing import Literal

from app.core.config import settings
from app.core import security
from app.crud.crud_auth_setting import auth_setting
from app.crud.crud_user import user as crud_user
from app.crud.crud_apikey import apikey
from app import crud
from app.schemas import SearchTypeMapping
from app.models import User, Role
from app.db.session import SessionLocal
from app.enums import AuthTypeEnum, TargetTypeEnum, PermissionEnum
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
        return crud_user.get_by_username(db, username=username)
    return None


class APIAuthMiddleware(Middleware):
    def __init__(self, client, *args, **kwargs):
        self.client = client
        self.semaphore = asyncio.Semaphore()
        return super().__init__(*args, **kwargs)

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        token = get_access_token()
        if not token:
            raise ToolError("Not authenticated")
        username = token.claims.get("preferred_username")
        if username and "@" in username and un_email_usernames:
            username = username.split("@")[0]
        async with self.semaphore:
            # Need a semaphore here so that race conditions don't alter the
            # authorization header between calls
            if username:
                new_jwt_token = security.create_access_token(
                    username, expires_delta=timedelta(seconds=5)
                )
                self.client.headers["authorization"] = "Bearer " + new_jwt_token
            elif token and token.client_id == "apikey-client":
                self.client.headers["authorization"] = "apikey " + token.token
            elif token:
                self.client.headers["authorization"] = "Bearer " + token.token
            result = await call_next(context)
            del self.client.headers["authorization"]
            return result


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
    keydata = apikey.get(SessionLocal(), token)
    if keydata is not None:
        request.state.user = keydata.owner
        return True
    return False


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
    # Grab the search endpoint from FastAPI
    client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=base_app),
        base_url="http://fastapi"
    )

    # Alter the description of the search endpoint to be more helpful to AI
    def customize_description(route, component: OpenAPITool | OpenAPIResource):
        if "search" in component.tags:
            component.description = """
            Perform a search across all SCOT text data (entries, alerts, and titles), optionally
            filtering by certain fields of the parent object. Results contain an `index_id` field
            that begins with \"a\" if the result is an alert or \"e\" if the result is an entry,
            followed by the id of that alert/entry. For alerts, the returned `entry_text` field is
            a dictionary of that alert's fields, while for entries it is a snippet of that entry's
            plain text content. The `target_type` and `target_id` fields represent the parent
            object of the entry/alert, while `parent_text` is the title of the parent object. If
            you know which types of objects are likely to contain the information you're searching
            for, it is best to filter by target_type to include only the most relevant results.
            Use a larger `crop_length` if you need more contextual information around the searched
            term(s). Finally, use the `limit` and `offset` parameters if you need to paginate your
            search results or get more results from a previous search. Do not repeat identical
            searches otherwise.
            """
    provider = OpenAPIProvider(
        openapi_spec=base_app.openapi(),
        client=client,
        route_maps=[
            RouteMap(tags={"search"}, mcp_type=MCPType.TOOL),
            RouteMap(mcp_type=MCPType.EXCLUDE)
        ],
        mcp_component_fn=customize_description
    )
    mcp = FastMCP(
        auth=auth,
        name="SCOT MCP Server",
        instructions="The Sandia Cyber Omni Tracker (SCOT) is a cyber security incident response management system and knowledge base.",
        providers=[provider]
    )
    mcp.add_middleware(APIAuthMiddleware(client))

    @mcp.resource(uri="resource://object/{object_type}/{object_id}", mime_type="text/markdown")
    def object_resource(object_type: TargetTypeEnum, object_id: int, db: Session = Depends(get_db), user: User = Depends(get_user)):
        """
        Retrieves a single SCOT object of the specified type by id,
        and provides it in markdown format
        """
        if object_type in deps.PermissionCheck.type_allow_whitelist:
            roles = None  # Don't check roles if an element does not have permissions (like entities, tags, sources, etc.)
        else:
            roles = user.roles
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
    def get_object(object_type: TargetTypeEnum, object_id: int, db: Session = Depends(get_db), user: User = Depends(get_user)):
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
            roles = user.roles
        try:
            deps.PermissionCheckId(object_type, PermissionEnum.read)(object_id, db, user, roles)
        except Exception as e:
            raise ToolError(e.message)
        object_crud = CRUDBase.target_crud_mapping.get(object_type)
        obj = object_crud.get(db, object_id)
        if obj:
            entries, _count = crud.entry.get_by_type(db, _type=object_type, _id=object_id, roles=roles)
            obj.plain_text_entries = [entry.entry_data.get("plain_text") for entry in entries]
        return jsonable_encoder(obj)

    @mcp.tool
    def search_objects(
        object_type: TargetTypeEnum,
        filters: dict,
        skip: int = 0,
        limit: int = 100,
        sort: str | None = None,
        db: Session = Depends(get_db),
        user: User = Depends(get_user),
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
            roles = user.roles
        try:
            search_obj = SearchTypeMapping[object_type](**filters)
            filter_dict = get_search_filters(search_obj)
            object_crud = CRUDBase.target_crud_mapping.get(object_type)
            _result, _count = object_crud.query_with_filters(db, roles, filter_dict, sort, skip, limit)
        except ValueError as e:
            raise ToolError(str(e))
        return jsonable_encoder({"totalCount": _count, "resultCount": len(_result), "result": _result})

    @mcp.tool
    def get_object_entries(
        object_type: TargetTypeEnum,
        object_id: int,
        skip: int = 0,
        limit: int = 100,
        entry_type: Literal["plain", "flaired", "all"] = "plain",
        db: Session = Depends(get_db),
        user: User = Depends(get_user),
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
            roles = user.roles
        try:
            deps.PermissionCheckId(object_type, PermissionEnum.read)(object_id, db, user, roles)
        except Exception as e:
            raise ToolError(e.message)
        _entries, count = crud.entry.get_by_type(db, roles=roles, _id=object_id, _type=object_type, skip=skip, limit=limit)
        for entry in _entries:
            if entry_type == "plain" and "plain_text" in entry.entry_data:
                entry.entry_data = {"plain_text": entry.entry_data["plain_text"]}
            elif entry_type == "flaired" and "flaired_html" in entry.entry_data:
                entry.entry_data = {"flaired_html": entry.entry_data["flaired_html"]}
        return jsonable_encoder({"totalCount": count, "resultCount": len(_entries), "result": _entries})

    @mcp.tool
    def read_entities(object_type: TargetTypeEnum, object_id: int, db: Session = Depends(get_db), user: User = Depends(get_user)):
        """
        Get all of the entities (e.g. domains, ip addresses, hashes) associated with a SCOT object
        """
        deps.PermissionCheckId(object_type, PermissionEnum.read)(object_id, db, user, user.roles)
        _entities, count = crud.entity.retrieve_element_entities(db, object_id, object_type)
        return jsonable_encoder({"totalCount": count, "resultCount": len(_entities), "result": _entities})

    @mcp.tool
    def download_file(file_id: int, db: Session = Depends(get_db)):
        """
        Download a file from SCOT
        """
        fileobj = crud.file.get(db, file_id)
        if fileobj is None:
            raise HTTPException(404, f"File {file_id} not found")
        try:
            filestream = crud.file.get_content(db, fileobj)
        except Exception as e:
            raise HTTPException(500, f"Could not retrieve file {file_id} data from storage - {e}")

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
