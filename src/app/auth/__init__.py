from app.enums import AuthTypeEnum

from .aad import AzureAdAuthentication
from .ldap import LdapAuthentication
from .local import LocalAuthentication

auth_classes = {
    AuthTypeEnum.ldap: LdapAuthentication,
    AuthTypeEnum.local: LocalAuthentication,
    AuthTypeEnum.aad: AzureAdAuthentication,
}

auth_objects = {}

# Get the authenticating class for a type of auth


def get_authenticator(auth_method):
    if auth_method.id in auth_objects:
        auth_object = auth_objects.get(auth_method.id)[0]
        saved_auth_properties = auth_objects.get(auth_method.id)[1]
        if auth_method.auth_properties == saved_auth_properties:
            # The session's auth storage object is passed as an attribute
            auth_object.storage = auth_method.storage
            return auth_object
        else:
            auth_class = auth_classes.get(auth_method.auth)
            if auth_class:
                new_auth_object = auth_class(auth_method.auth_properties)
                auth_objects[auth_method.id] = (new_auth_object,
                    auth_method.auth_properties)
                new_auth_object.storage = auth_method.storage
                return new_auth_object
            else:
                return None
    elif auth_method.auth in auth_classes:
        auth_class = auth_classes.get(auth_method.auth)
        new_auth_object = auth_class(auth_method.auth_properties)
        auth_objects[auth_method.id] = (new_auth_object,
            auth_method.auth_properties)
        new_auth_object.storage = auth_method.storage
        return new_auth_object
    else:
        return None
