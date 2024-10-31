import os

from streaming_form_data.targets import BaseTarget
from .base import BaseStorageProvider
import boto3
import string
import random
import logging
import traceback


class SCOTS3Target(BaseTarget):
    def __init__(self, filename=None, bucket=None, s3_client: boto3.client = None):
        super().__init__()
        self.filename = filename
        self.s3_client = s3_client
        self.bucket = bucket
        self.upload_obj = self.s3_client.create_multipart_upload(Bucket=self.bucket, Key=self.filename)
        self.part_number = 1
        self.parts = []

    def on_data_received(self, chunk):
        upload_part_response = self.s3_client.upload_part(
            Body=chunk,
            Bucket=self.bucket,
            Key=self.filename,
            PartNumber=self.part_number,
            UploadId=self.upload_obj['UploadId'])
        self.parts.append({'PartNumber': self.part_number, 'ETag': upload_part_response['ETag']})
        self.part_number += 1

    def on_finish(self):
        self.s3_client.complete_multipart_upload(Bucket=self.bucket, Key=self.filename, MultipartUpload={'Parts': self.parts},
                                                 UploadId=self.upload_obj['UploadId'])


"""
Abstraction of Dell EMC S3 Storage Provider
"""


class DellEMCS3StorageProvider(BaseStorageProvider):
    default_config = {
        "provider_name": "",
        "key": "",
        "host": "https://yourhosthere",
        "secret": "",
        "port": "",
        "root_bucket": "",
        "no_proxy": "",
        "http_proxy": "",
        "deleted_items_location": "",
        "emc_namespace": ""



    }

    config_name_pretty = {
        "provider_name": "Provider Name",
        "key": "API Access Key",
        "host": "Storage Account Endpoint",
        "secret": "API Secret Access Key",
        "port": "Storage Account Endpoint Port",
        "root_bucket": "Base Bucket Path",
        "no_proxy": "No Proxy env variable",
        "http_proxy": "HTTP proxy env variable",
        "deleted_items_location": "Deleted Items Bucket",
        "emc_namespace": "EMC Namespace"

    }

    config_help = {
        "provider_name": "A name that identifies this authentication instance",
        "key": "API Access Key",
        "host": "Storage Account Endpoint",
        "secret": "API Secret Access Key",
        "port": "Storage Account Endpoint Port",
        "root_bucket": "The path of the base bucket where objects will be stored under",
        "no_proxy": "Set the NO_PROXY environment variable for this object storage connection",
        'http_proxy': "Set the HTTP/HTTPS environment variables for this object storage connection",
        "emc_namespace": "The EMC Namespace for the object storage",
        "deleted_items_location": "Bucket where deleted files will be temporarily moved to."
    }

    def __init__(self, filename=None, **kwargs):
        self.namespace = kwargs['emc_namespace']
        self.host = kwargs['host']
        self.port = kwargs['port']
        if self.host[:5] == 'https':
            self.secure = True
        else:
            self.secure = False

        self.full_uri = f"{self.host}:{self.port}"
        # Your AWS access key ID is also known in ECS as your object user
        self.access_key = kwargs['key']
        self.deleted_items_location = kwargs['deleted_items_location']
        self.secret_key = kwargs['secret']
        self.root_bucket = kwargs['root_bucket']
        # The secret key that belongs to your object user.
        self.s3_client = boto3.client('s3', aws_access_key_id=self.access_key, aws_secret_access_key=self.secret_key, use_ssl=self.secure,
                                      endpoint_url=self.full_uri)
        event_system = self.s3_client.meta.events
        event_system.register_first('before-sign.*.*', self._add_header)

    def _add_header(self, request, **kwargs):
        request.headers.add_header('x-emc-namespace', self.namespace)

    def get_target(self, filename=None):
        target = SCOTS3Target(filename=filename, bucket=self.root_bucket, s3_client=self.s3_client)
        return target

    def get_file_handle(self, filename=None):
        return self.s3_client.get_object(Bucket=self.root_bucket, Key=filename)['Body']

    def move_file_to_deleted_location(self, filename=None):
        copy_from = f"{self.root_bucket}/{filename}"
        self.s3_client.copy_object(Bucket=self.deleted_items_location, Key=filename, CopySource=copy_from)
        return self.s3_client.delete_object(Bucket=self.root_bucket, Key=filename)

    def move_file_to_default_location(self, filename=None):
        copy_from = f"{self.deleted_items_location}/{filename}"
        self.s3_client.copy_object(Bucket=self.root_bucket, Key=filename, CopySource=copy_from)
        return self.s3_client.delete_object(Bucket=self.deleted_items_location, Key=filename)

    def sanity_check(self) -> bool:
        """ Simply going to write and read from both buckets. If it all works return True

        """
        try:
            fileSizeInBytes = 1024
            letters = string.ascii_lowercase
            file_name = "".join(random.choices(letters, k=30))  # nosec
            file_path = f"/tmp/{file_name}"  # nosec
            with open(file_path, 'wb') as fout:
                fout.write(os.urandom(fileSizeInBytes))  # replace 1024 with a size in kilobytes if it is not unreasonably large
            self.s3_client.upload_file(file_path, self.root_bucket, file_name)
            self.s3_client.get_object(Bucket=self.root_bucket, Key=file_name)
            self.s3_client.delete_object(Bucket=self.root_bucket, Key=file_name)

            self.s3_client.upload_file(file_path, self.deleted_items_location, file_name)
            self.s3_client.get_object(Bucket=self.deleted_items_location, Key=file_name)
            self.s3_client.delete_object(Bucket=self.deleted_items_location, Key=file_name)
            os.remove(file_path)
            return True

        except Exception:
            logging.error(traceback.format_exc())
            return False
