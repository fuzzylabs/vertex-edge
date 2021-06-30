import os.path
from serde import serialize, deserialize
from serde.yaml import to_yaml, from_yaml
from dataclasses import dataclass
from google.cloud import storage

from edge.config import EdgeConfig
from typing import Type, TypeVar


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
        client = storage.Client()
        bucket = client.bucket(_config.storage_bucket.bucket_name)
        blob = storage.Blob(".edge_state/edge_state.yaml", bucket)
        blob.upload_from_string(to_yaml(self))

    @classmethod
    def load(cls: Type[T], _config: EdgeConfig) -> T:
        client = storage.Client()
        bucket = client.bucket(_config.storage_bucket.bucket_name)
        blob = storage.Blob(".edge_state/edge_state.yaml", bucket)
        return from_yaml(EdgeState, blob.download_as_bytes(client).decode("utf-8"))
