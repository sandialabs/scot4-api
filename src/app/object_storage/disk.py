import os
import shutil

from .base import BaseStorageProvider
from streaming_form_data.targets import FileTarget
import string
import random
import traceback
import logging
"""
Abstraction of LocalStorageProvider
"""


class DiskStorageProvider(BaseStorageProvider):
    default_config = {
        "provider_name": "",
        "root_directory": "",
        "deleted_items_directory": ""
    }
    config_name_pretty = {"provider_name": "Provider Name", "root_directory": "Base Directory", "deleted_items_directory": "Deleted Items Directory"}
    config_help = {
        "provider_name": "A name that identifies this storage provider instance",
        "root_directory": "Base directory of local file system",
        "deleted_items_directory": "Directory where deleted files will be temporarily moved to."
    }

    def __init__(self, **kwargs):
        self.deleted_items_folder = kwargs.get('deleted_items_directory')
        if self.deleted_items_folder[-1] == '/':
            self.deleted_items_folder = self.deleted_items_folder[:-1]
        self.root_directory = kwargs.get('root_directory')
        if self.root_directory[-1] == '/':
            self.root_directory = self.root_directory[:-1]

    def get_target(self, filename=None):
        file_path = f"{self.root_directory}/{filename}"
        return FileTarget(file_path)

    def get_file_handle(self, filename=None):
        file_path = f"{self.root_directory}/{filename}"
        return open(file_path, 'rb')

    def move_file_to_deleted_location(self, filename=None):
        file_path = f"{self.root_directory}/{filename}"
        del_file_path = f"{self.deleted_items_folder}/{filename}"
        shutil.move(file_path, del_file_path)

    def move_file_to_default_location(self, filename=None):
        file_path = f"{self.root_directory}/{filename}"
        del_file_path = f"{self.deleted_items_folder}/{filename}"
        shutil.move(del_file_path, file_path)

    def sanity_check(self) -> bool:
        """ Simply going to write to each directory. If it all works return True

        """
        try:
            fileSizeInBytes = 1024
            letters = string.ascii_lowercase
            file_name = "".join(random.choices(letters, k=30))  # nosec
            file_path = f"{self.root_directory}/{file_name}"
            deleted_path = f"{self.deleted_items_folder}/{file_name}"

            with open(file_path, 'wb') as fout:
                fout.write(os.urandom(fileSizeInBytes))  # replace 1024 with a size in kilobytes if it is not unreasonably large
            os.remove(file_path)

            with open(deleted_path, 'wb') as fout:
                fout.write(os.urandom(fileSizeInBytes))  # replace 1024 with a size in kilobytes if it is not unreasonably large
            os.remove(deleted_path)

            return True

        except Exception:
            logging.error(traceback.format_exc())
            return False
