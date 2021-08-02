import sys
from typing import Optional
from serde import serialize, deserialize
from dataclasses import dataclass
from google.api_core.exceptions import NotFound, Forbidden
from google.cloud import storage
from .config import EdgeConfig
from .exception import EdgeException
from .tui import (
    print_substep_not_done, print_substep_success, print_substep_failure, print_failure_explanation, print_substep,
    clear_last_line, SubStepTUI
)


@deserialize
@serialize
@dataclass
class StorageBucketState:
    bucket_path: str


def get_bucket(project_id: str, bucket_name: str) -> Optional[storage.Bucket]:
    try:
        client = storage.Client(project_id)
        bucket = client.get_bucket(bucket_name)
        return bucket
    except NotFound:
        return None
    except Forbidden:
        raise EdgeException(
            f"The bucket '{bucket_name}' exists, but you do not have permissions to access it. "
            "Maybe it belongs to another project? "
            "Please see the following guidelines for more information "
            "https://cloud.google.com/storage/docs/naming-buckets"
        )


def get_bucket_uri(project_id: str, bucket_name: str) -> Optional[str]:
    bucket = get_bucket(project_id, bucket_name)
    if bucket is None:
        return None
    return f"gs://{bucket.name}/"


def create_bucket(project_id: str, region: str, bucket_name: str) -> str:
    client = storage.Client(project_id)
    bucket = client.create_bucket(bucket_or_name=bucket_name, project=project_id, location=region)
    return f"gs://{bucket.name}/"


def delete_bucket(project_id: str, region: str, bucket_name: str):
    client = storage.Client(project_id)
    bucket = client.get_bucket(bucket_name)
    print("## Deleting bucket content")
    bucket.delete_blobs(blobs=list(bucket.list_blobs()))
    print("## Deleting bucket")
    bucket.delete(force=True)
    print("Bucket deleted")


def tear_down_storage(_config: EdgeConfig, _state):
    print("# Tearing down Google Storage")
    bucket_path = get_bucket_uri(
        _config.google_cloud_project.project_id,
        _config.storage_bucket.bucket_name,
    )
    if bucket_path is not None:
        delete_bucket(
            _config.google_cloud_project.project_id,
            _config.google_cloud_project.region,
            _config.storage_bucket.bucket_name,
        )


def setup_storage(project_id: str, region: str, bucket_name: str) -> StorageBucketState:
    with SubStepTUI(f"Checking if '{bucket_name}' exists") as sub_step:
        try:
            bucket_path = get_bucket_uri(
                project_id,
                bucket_name,
            )
            if bucket_path is None:
                clear_last_line()
                sub_step.update(message=f"'{bucket_name}' does not exist, creating it")
                bucket_path = create_bucket(
                    project_id,
                    region,
                    bucket_name,
                )
            return StorageBucketState(bucket_path)
        except NotFound as e:
            raise EdgeException(f"The '{project_id}' project could not be found. It might mean that the quota project "
                                f"is set to a different project. Please generate new application default "
                                f"credentials by running `gcloud auth application-default login`")
        except ValueError as e:
            raise EdgeException(f"Unexpected error while setting up Storage bucket:\n{str(e)}")
