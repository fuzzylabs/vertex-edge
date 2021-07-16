from typing import Optional
from serde import serialize, deserialize
from dataclasses import dataclass
from google.api_core.exceptions import NotFound, Forbidden
from google.cloud import storage
from .config import EdgeConfig


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
        print(f"Error: the bucket [{bucket_name}] exists, but you do not have permissions to access it. Maybe it "
              f"belongs to another project? For more information on bucket naming see: "
              f"https://cloud.google.com/storage/docs/naming-buckets")
        exit(1)


def get_bucket_uri(project_id: str, bucket_name: str) -> Optional[str]:
    print(f"## Checking if {bucket_name} bucket exists")
    bucket = get_bucket(project_id, bucket_name)
    if bucket is None:
        return None
    print(f"Bucket found: gs://{bucket.name}/")
    return f"gs://{bucket.name}/"


def create_bucket(project_id: str, region: str, bucket_name: str) -> str:
    print(f"## Creating '{bucket_name}' bucket")
    client = storage.Client(project_id)
    bucket = client.create_bucket(
        bucket_or_name=bucket_name,
        project=project_id,
        location=region
    )
    print(f"Bucket created: gs://{bucket.name}/")
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


def setup_storage(_config: EdgeConfig) -> StorageBucketState:
    print("# Setting up Google Storage")
    bucket_path = get_bucket_uri(
        _config.google_cloud_project.project_id,
        _config.storage_bucket.bucket_name,
    )
    if bucket_path is None:
        print(f"'{_config.storage_bucket.bucket_name}' bucket does not exist")
        bucket_path = create_bucket(
            _config.google_cloud_project.project_id,
            _config.google_cloud_project.region,
            _config.storage_bucket.bucket_name,
        )
    return StorageBucketState(
        bucket_path
    )
