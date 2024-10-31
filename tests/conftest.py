import time
import msal.authority
import pytest
from typing import Generator
from urllib.parse import parse_qs, urlparse
from faker import Faker
from fastapi.testclient import TestClient
from msal import ConfidentialClientApplication
from requests import Session
from sqlalchemy.orm import Session as SqlalchemySession

from app import crud
from app.core.config import settings
from app.db import init_db
from app.db.session import SessionLocal
from app.enums import AuthTypeEnum
from app.main import app
from app.schemas import AuthSettingsCreate

from utils.user import authentication_token_from_username
from utils.utils import get_superuser_token_headers


@pytest.fixture(scope="session", autouse=True)
def db_mutable() -> Generator:
    session = SessionLocal()
    init_db.init_db(session, create_tables=True, reset_db=False)
    yield session
    session.close()


# Default fixture rolls back after every test
@pytest.fixture(scope="function")
def db(db_mutable: SqlalchemySession) -> Generator:
    yield db_mutable
    db_mutable.rollback()
    db_mutable.close()


@pytest.fixture(scope="module")
def client() -> Generator:
    with TestClient(app) as c:
        yield c


# Replace default pytest faker with global session instance
@pytest.fixture(scope="session")
def faker() -> Faker:
    return Faker()


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(
    client: TestClient, db_mutable: Session, faker: Faker
) -> dict[str, str]:
    return authentication_token_from_username(
        client=client, username=settings.EMAIL_TEST_USER, db=db_mutable, faker=faker
    )


@pytest.fixture(scope="function")
def user_data(faker: Faker) -> dict:
    test_user_data = {
        faker.user_name(): {
            "userPassword": faker.password(),
            "email": faker.email(),
            "displayName": faker.name(),
            "memberOf": ["cn=group1,ou=groups,dc=test"],
        },
        faker.user_name(): {
            "userPassword": faker.password(),
            "email": faker.email(),
            "displayName": faker.name(),
            "memberOf": ["cn=group2,ou=groups,dc=test"],
        },
        faker.user_name(): {
            "userPassword": faker.password(),
            "email": faker.email(),
            "displayName": faker.name(),
            "memberOf": ["cn=group1,ou=groups,dc=test", "cn=group2,ou=groups,dc=test"],
        },
    }
    return test_user_data


@pytest.fixture(scope="function")
def ldap_test_settings(user_data: dict, db: Session):
    user_base_dn = "ou=users,dc=test"
    group_base_dn = "ou=groups,dc=test"
    mock_data = {}
    group_1_membership = [
        "uid=%s,%s" % (u, user_base_dn)
        for u in user_data
        if "cn=group1,ou=groups,dc=test" in user_data[u]["memberOf"]
    ]
    group_2_membership = [
        "uid=%s,%s" % (u, user_base_dn)
        for u in user_data
        if "cn=group2,ou=groups,dc=test" in user_data[u]["memberOf"]
    ]
    for user in user_data:
        mock_data["uid=%s,%s" % (user, user_base_dn)] = user_data[user]
    mock_data["cn=group1,ou=groups,dc=test"] = {"uniqueMember": group_1_membership}
    mock_data["cn=group2,ou=groups,dc=test"] = {"uniqueMember": group_2_membership}
    config = {
        "provider_name": "test_provider",
        "server": "test_server",
        "bind_user": None,
        "bind_password": None,
        "test_user": list(user_data)[0],
        "test_group": "group1",
        "username_attribute": "uid",
        "user_email_attribute": "email",
        "user_full_name_attribute": "displayName",
        "user_group_attribute": "memberOf",
        "user_base_dn": user_base_dn,
        "user_filter": "",
        "group_base_dn": group_base_dn,
        "group_filter": "",
        "group_member_attribute": "uniqueMember",
        "group_name_attribute": "cn",
        "group_autocreate": True,
        "mock_data": mock_data,
    }
    new_auth_settings = AuthSettingsCreate(
        auth=AuthTypeEnum.ldap, auth_properties=config
    )
    return crud.auth_setting.create_auth_method(db, new_auth=new_auth_settings)


@pytest.fixture(scope="function")
def azuread_test_settings(db: Session, faker: Faker, monkeypatch):
    # Patch the auth code flow initiation to return a fixed flow dictionary
    fake_login_state = faker.pystr()

    def fake_init_auth_code_flow(self, scopes, **kwargs):
        return {
            # A real auth uri will have more here, but this is just a test
            "auth_uri": self.authority.authorization_endpoint
            + "?state="
            + fake_login_state,
            "state": fake_login_state,
        }

    def fake_acquire_token_by_auth_code_flow(
        self, auth_code_flow, auth_response, scopes=None, **kwargs
    ):  # Patch the actual authorization endpoint
        # In our test flow, id_token is just a dictionary of user attributes
        id_token = auth_response["id_token"]
        return {"id_token_claims": id_token, "id_token": id_token, "access_token": {}}

    # Patch __init__ to set validate_authority to False
    # old_init = ConfidentialClientApplication.__init__
    # def fake_init(*args, **kwargs):
    #     kwargs["validate_authority"] = False
    #     return old_init(*args, **kwargs)

    def fake_tenant_discovery(
        *args, **kwargs
    ):  # Patch authority instance discovery to not go out
        return {
            "authorization_endpoint": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            "token_endpoint": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        }

    def fake_request(
        *args, **kwargs
    ):  # Patch requests to make sure no actual requests go out
        raise Exception("Can't go to internet")

    # Do the monkeypatching
    monkeypatch.setattr(
        ConfidentialClientApplication,
        "initiate_auth_code_flow",
        fake_init_auth_code_flow,
    )
    monkeypatch.setattr(
        ConfidentialClientApplication,
        "acquire_token_by_auth_code_flow",
        fake_acquire_token_by_auth_code_flow,
    )
    # monkeypatch.setattr(ConfidentialClientApplication, "__init__", fake_init)
    monkeypatch.setattr(msal.authority, "tenant_discovery", fake_tenant_discovery)
    monkeypatch.setattr(Session, "get", fake_request)
    monkeypatch.setattr(Session, "post", fake_request)
    # Create the actual AuthSettings object
    aad_config = {
        "client_id": "00000000-0000-0000-0000-000000000000",
        "client_secret": faker.pystr(),
        "authority": "https://login.microsoftonline.com/common",
        "callback_url": "http://example.com/callback",
        "scope": ["User.Read"],
        "group_autocreate": True,
    }
    new_auth_settings = AuthSettingsCreate(
        auth=AuthTypeEnum.aad, auth_properties=aad_config
    )
    return crud.auth_setting.create_auth_method(db, new_auth=new_auth_settings)


# This fixture is for fake users to fake-authenticate to microsoft online and
# returns a callable that simulates that
@pytest.fixture(scope="function")
def azuread_fake_auth_endpoint(user_data: dict):
    def login_function(username: str, url: str):
        # Piggyback off of generated ldap user data
        one_user_data = user_data.get(username)
        if one_user_data is None:
            raise ValueError("User not found in fake aad auth")
        state = parse_qs(urlparse(url).query)["state"][0]
        # The token is just a flat dictionary instead of a signed json token
        id_token = {
            "exp": time.time() + 60,
            "oid": "00000000-0000-0000-0000-000000000000",
            "upn": username,
            "unique_name": username,
            "roles": [group[3:9] for group in one_user_data["memberOf"]],
            "email": one_user_data["email"],
            "name": one_user_data["displayName"],
        }
        return {"state": state, "id_token": id_token, "code": "fake_code"}

    return login_function
