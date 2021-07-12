from typing import Optional
from google.api_core.exceptions import NotFound
from google.cloud import storage
from .config import EdgeConfig
from .state import StorageBucketState, EdgeState


def get_bucket(project_id: str, bucket_name: str) -> Optional[str]:
    print(f"## Checking if {bucket_name} bucket exists")
    try:
        client = storage.Client(project_id)
        bucket = client.get_bucket(bucket_name)
    except NotFound:
        return None
    print(f"Bucket found: gs://{bucket.name}/")
    return f"gs://{bucket.name}/"


def create_bucket(project_id: str, region: str, bucket_name: str) -> str:
    print(f"## Creating {bucket_name} bucket")
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


def tear_down_storage(_config: EdgeConfig, _state: EdgeState):
    print("# Tearing down Google Storage")
    bucket_path = get_bucket(
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
    bucket_path = get_bucket(
        _config.google_cloud_project.project_id,
        _config.storage_bucket.bucket_name,
    )
    if bucket_path is None:
        print(f"{_config.storage_bucket.bucket_name} bucket does not exist")
        bucket_path = create_bucket(
            _config.google_cloud_project.project_id,
            _config.google_cloud_project.region,
            _config.storage_bucket.bucket_name,
        )
    return StorageBucketState(
        bucket_path
    )
