import msal
import json
from datetime import datetime, timedelta

from app.schemas.user import UserCreate

from .base import BaseAuthentication

"""
Abstraction of aad auth
"""


class AzureAdAuthentication(BaseAuthentication):
    default_config = {
        "provider_name": "",
        "client_id": "",
        "client_secret": "",
        "authority": "https://login.microsoftonline.com/common",
        "callback_url": "",
        "scopes": [],
        "un_email_usernames": False,
        "access_roles": [],
        "group_autocreate": True,
        "certificate_authority": ""
    }

    config_name_pretty = {
        "provider_name": "Provider Name",
        "client_id": "Client ID",
        "client_secret": "Client Secret",
        "authority": "Authority",
        "callback_url": "Callback URL",
        "scopes": "Scopes",
        "un_email_usernames": "Un-Email Usernames",
        "access_roles": "Access Roles",
        "group_autocreate": "Auto-create Groups",
        "certificate_authority": "Certificate Authority Bundle"
    }

    config_help = {
        "provider_name": "A name that identifies this authentication instance",
        "client_id": "The client ID of your application in Azure Active"
        " Directory",
        "client_secret": "A client secret configured for your application in"
        " Azure Active Directory",
        "authority": "The authority used to log in to Azure; this is usually"
        " in the format https://login.microsoftonline.com/"
        "<tenant_id> or https://login.microsoftonline.com/"
        "common for authentication directly to microsoft",
        "callback_url": "The callback url configured for your SCOT instance,"
        " this should usually be the base of the SCOT GUI, e.g."
        " https://your-scot-instance.com/",
        "scopes": "The scopes to request when logging in (optional)",
        "un_email_usernames": "Whether or not to attempt to convert the"
        + " username provided by Azure out of email address format"
        + " (dropping the portion after the @)",
        "access_roles": "If set, users will be required to have the given"
        + " application role in order to log in",
        "group_autocreate": "When set, SCOT will auto-create roles matching"
        + " the names of all configured application roles when a"
        + " user logs in",
        "certificate_authority": "When set to a path, the given certificate"
        + " bundle is used instead of the default certificate"
        + " bundle. Useful if the network is behind an intercepting"
        + " proxy."
    }

    def __init__(self, config):
        self.token_endpoint = config.get("token_endpoint", None)
        self.client_id = config.get("client_id", None)
        self.client_secret = config.get("client_secret", None)
        self.authority = config.get("authority", None)
        self.callback_url = config.get("callback_url", None)
        self.scopes = config.get("scope", [])
        self.un_email_usernames = config.get("un_email_usernames", False)
        self.group_autocreate = config.get("group_autocreate", True)
        self.access_roles = config.get("access_roles", None)
        self.certs = config.get("certificate_authority", None)
        if not self.certs:
            self.certs = True
        # Coerce access_roles to list
        if self.access_roles and isinstance(self.access_roles, str):
            self.access_roles = [self.access_roles]
        if self.client_id:
            self.app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=self.authority,
                verify=self.certs)
        else:
            self.app = None
        self.storage = None

    def authenticate_password(self, username, password, user=None):
        raise NotImplementedError()

    def start_external_authenticate(self, user=None):
        if not self.app:
            raise ValueError("AAD auth not configured")
        flow = self.app.initiate_auth_code_flow(
            self.scopes, redirect_uri=self.callback_url
        )
        state = flow["state"]
        flow["_scot_datetime"] = datetime.utcnow().isoformat()
        self.storage[state] = json.dumps(flow)
        return flow["auth_uri"]

    def authenticate_token(self, token, user=None):
        if not self.app:
            raise ValueError("AAD auth not configured")
        state = token.get("state")
        if state not in self.storage:
            raise ValueError("CSRF token mismatch during AAD authentication")
        flow = json.loads(self.storage[state])
        del flow["_scot_datetime"]
        del self.storage[state]
        auth_result = self.app.acquire_token_by_auth_code_flow(flow, token)
        # Clean up all old flows older than an hour
        if len(self.storage) > 0:
            expiry = (datetime.utcnow() + timedelta(hours=1)).isoformat()
            for key, value in list(self.storage.items()):
                item = json.loads(value)
                if (
                    not item.get("_scot_datetime")
                    or item.get("_scot_datetime") < expiry
                ):
                    del self.storage[key]

        # Grab stuff from the ID Token
        if "error" in auth_result:
            error = auth_result.get("error")
            error_description = auth_result.get("error_description", "Unknown")
            raise ValueError("Error (%s): %s" % (error, error_description))
        token_info = auth_result.get("id_token_claims", {})
        username = token_info.get("preferred_username", None)
        roles = token_info.get("roles", [])
        # Deny login if user doesn't have one of the required access roles
        if self.access_roles and set(roles).isdisjoint(self.access_roles):
            return None
        # Collect user metadata
        if username is None:
            username = token_info.get("unique_name", None)
        if self.un_email_usernames and username and "@" in username:
            # Unique_name is often an email, strip off the part after the @
            username = username.split("@")[0]
        user_email = token_info.get("email", None)
        user_full_name = token_info.get("name", None)
        return UserCreate(
            username=username, email=user_email,
            fullname=user_full_name, roles=roles
        )
