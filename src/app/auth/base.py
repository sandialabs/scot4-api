from abc import ABC, abstractmethod


class BaseAuthentication(ABC):
    # The default config created when an authentication method of this type
    # is created
    default_config = {"provider_name": "DEFAULT AUTH"}

    # The "pretty name" of each config option
    config_name_pretty = {"provider_name": "Provider Name"}

    # Optional help text for each config field for this type of auth
    config_help = {
        "provider_name": "A name that identifies this authentication instance",
    }

    @abstractmethod
    def __init__(self, config):
        """
        This method should take a stored config for that particular auth method
        (see enums.py) and construct an auth object
        """
        pass

    @abstractmethod
    def authenticate_password(self, username, password, user=None):
        """
        This method should be called when the user wants to authenticate
        with a password. If this auth method does not support password-based
        authentication, it should raise a NotImplementedError. Otherwise, it
        should return None if authentication was not successful, or a truthy
        object if it was.
        The calling method can optionally pass the db user object corresponding
        to that username. If this object is None, the method MUST return a
        user schema object corresponding to the user to be created (if auth
        is successful).
        """
        pass

    @abstractmethod
    def start_external_authenticate(self, user=None):
        """
        This method should be called when a user wishes to authenticate with
        an external authentication method. It should return a url to redirect
        to for authentication, or raise NotImplementedError if this is not
        supported.
        The calling method can optionally pass the db user object corresponding
        to the user to authenticate.
        """
        pass

    @abstractmethod
    def authenticate_token(self, username, token, user=None):
        """
        This method should be called for non-password-based authentication
        based on data provided in token. This can also be the second step
        in external authentication started with start_external_authentication.
        It should return a truthy object if authentication was successful,
        or None if it wasn't, or raise NotImplementedError if this is not
        supported.
        The calling method can optionally pass the db user object corresponding
        to that username. If this object is None, the method MUST return a
        user schema object corresponding to the user to be created (if auth
        is successful).
        """
        pass
