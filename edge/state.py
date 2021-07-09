import os.path
from serde import serialize, deserialize
from serde.yaml import to_yaml, from_yaml
from dataclasses import dataclass
from google.cloud import storage

from edge.config import EdgeConfig
from typing import Type, TypeVar, Optional


@deserialize
@serialize
@dataclass
class SacredState:
    external_omniboard_string: str


@deserialize
@serialize
@dataclass
class VertexEndpointState:
    endpoint_resource_name: str


@deserialize
@serialize
@dataclass
class StorageBucketState:
    bucket_path: str


T = TypeVar('T', bound='EdgeState')


@deserialize
@serialize
@dataclass
class EdgeState:
    vertex_endpoint_state: VertexEndpointState
    sacred_state: SacredState
    storage_bucket_state: StorageBucketState

    def save(self, _config: EdgeConfig):
        client = storage.Client(project=_config.google_cloud_project.project_id)
        bucket = client.bucket(_config.storage_bucket.bucket_name)
        blob = storage.Blob(".edge_state/edge_state.yaml", bucket)
        blob.upload_from_string(to_yaml(self))

    @classmethod
    def load(cls: Type[T], _config: EdgeConfig) -> Optional[T]:
        client = storage.Client(project=_config.google_cloud_project.project_id)
        bucket = client.bucket(_config.storage_bucket.bucket_name)
        blob = storage.Blob(".edge_state/edge_state.yaml", bucket)
        if blob.exists():
            return from_yaml(EdgeState, blob.download_as_bytes(client).decode("utf-8"))
        else:
            return None

    @classmethod
    def lock(cls, project: str, bucket_name: str, blob_name: str = ".edge_state/edge_state.yaml") -> (bool, bool):
        """
        Lock the state file in Google Storage Bucket

        :param bucket_name:
        :param blob_name:
        :return: (bool, bool) -- is lock successful, is state to be locked later
        """
        client = storage.Client(project=project)
        bucket = client.bucket(bucket_name)
        if not bucket.exists():
            print("Google Storage Bucket does not exist, lock later...")
            return False, True
        blob = storage.Blob(f"{blob_name}.lock", bucket)
        if blob.exists():
            print("State file is already locked")
            return False, False

        blob.upload_from_string("locked")
        print("State file locked")
        return True, False

    @classmethod
    def unlock(cls, project: str, bucket_name: str, blob_name: str = ".edge_state/edge_state.yaml"):
        client = storage.Client(project=project)
        bucket = client.bucket(bucket_name)
        blob = storage.Blob(f"{blob_name}.lock", bucket)
        if blob.exists():
            blob.delete()
        print("State file unlocked")
