from serde import serialize, deserialize
from dataclasses import dataclass


@deserialize
@serialize
@dataclass
class SacredState:
    # internal_mongo_string: str
    # external_mongo_string: str
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


@deserialize
@serialize
@dataclass
class EdgeState:
    vertex_endpoint_output: VertexEndpointState
    sacred_output: SacredState
    storage_bucket_output: StorageBucketState
