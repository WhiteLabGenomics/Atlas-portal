import contextlib
from typing import Iterable, List, Set
from urllib.parse import urlparse

from backend.layers.thirdparty.s3_provider_interface import S3ProviderInterface


class MockS3Provider(S3ProviderInterface):
    """
    Simple S3 mock that mostly checks if paths are correct
    """

    def __init__(self) -> None:
        self.mock_s3_fs: Set[str] = set()

    def parse_s3_uri(self, s3_uri: str):
        parsed_url = urlparse(s3_uri)
        return parsed_url.netloc, parsed_url.path[1:]

    def upload_file(self, src_file: str, bucket_name: str, dst_file: str, extra_args: dict):
        url = f"s3://{bucket_name}/{dst_file}"
        self.mock_s3_fs.add(url)

    def upload_directory(self, src_dir: str, s3_uri: str):
        self.mock_s3_fs.add(s3_uri)

    def delete_files(self, bucket_name: str, object_keys: List[str]):
        for key in object_keys:
            with contextlib.suppress(KeyError):  # if key is not in bucket
                self.mock_s3_fs.remove(f"s3://{bucket_name}/{key}")

    def delete_prefix(self, bucket_name: str, prefix: str) -> None:
        object_keys = list(self.list_directory(bucket_name, prefix))
        self.delete_files(bucket_name, object_keys)

    def download_file(self, bucket_name: str, object_key: str, local_filename: str):
        pass

    def restore_object(self, bucket_name: str, object_key: str) -> None:
        url = f"s3://{bucket_name}/{object_key}"
        self.mock_s3_fs.add(url)

    def file_exists(self, bucket_name: str, object_key: str):
        url = f"s3://{bucket_name}/{object_key}"
        return self.uri_exists(url)

    def list_directory(self, bucket_name: str, src_dir: str) -> Iterable[str]:
        object_prefix = f"s3://{bucket_name}/{src_dir}"
        for key in self.mock_s3_fs:
            if key.startswith(object_prefix):
                yield key

    def uri_exists(self, uri: str):
        return uri in self.mock_s3_fs

    def is_empty(self):
        return len(self.mock_s3_fs) == 0
