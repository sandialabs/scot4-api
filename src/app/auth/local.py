from app.core.security import verify_password
from app.schemas.user import UserCreate, User
from app.auth.base import BaseAuthentication

"""
Abstraction of local auth
Note this is should also be the fallback if AAD or LDAP fail
"""


class LocalAuthentication(BaseAuthentication):
    default_config = {"provider_name": "Local SCOT Auth"}

    def __init__(self, config: dict):
        # No config for local auth
        pass

    def authenticate_password(self, username: str, password: str, user: User | None = None):
        if user is None:
            return None
        if verify_password(password, user.pw_hash):
            # Users already have to be in the db for local auth
            return UserCreate(username=username)
        else:
            return None

    def start_external_authenticate(self, username: str, user: User | None = None):
        raise NotImplementedError()

    def authenticate_token(self, token: str, user: User | None = None):
        raise NotImplementedError()
