from abc import ABC, abstractmethod
from streaming_form_data.targets import BaseTarget
from typing import Any, Callable


class BaseStorageProvider(ABC):
    # The default config created when an authentication method of this type
    # is created
    default_config = {"provider_name": "STORAGE NAME"}

    # The "pretty name" of each config option
    config_name_pretty = {"provider_name": "Provider Name"}

    # Optional help text for each config field for this type of storage provider
    config_help = {
        "provider_name": "A name that identifies this storage provider instance",
    }

    @abstractmethod
    def __init__(self, config):
        """
        This method should take a stored config for that particular storage provider
        (see enums.py) and construct an storage provider object
        """
        pass

    @abstractmethod
    def get_target(self, filename=None):
        pass

    @abstractmethod
    def get_file_handle(self, filename=None):
        pass

    @abstractmethod
    def move_file_to_deleted_location(self, filename=None):
        pass

    @abstractmethod
    def sanity_check(self) -> bool:
        pass


class FileSizeTarget(BaseTarget):
    def __init__(self, validator: Callable[..., Any] = None):
        self.filesize = 0
        super().__init__(validator)

    def on_data_received(self, chunk: bytes):
        self.filesize += len(chunk)
