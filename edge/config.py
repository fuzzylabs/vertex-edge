from dataclasses import dataclass
from typing import TypeVar, Type, Optional
from serde import serialize, deserialize
from serde.yaml import from_yaml, to_yaml
import os


@deserialize
@serialize
@dataclass
class GCProjectConfig:
    project_id: str
    region: str


@deserialize
@serialize
@dataclass
class StorageBucketConfig:
    bucket_name: str
    dvc_store_directory: str
    vertex_jobs_directory: str


@deserialize
@serialize
@dataclass
class SacredConfig:
    gke_cluster_name: str
    mongodb_connection_string_secret: str


@deserialize
@serialize
@dataclass
class VertexConfig:
    model_name: str
    prediction_server_image: str


@deserialize
@serialize
@dataclass
class WebAppConfig:
    webapp_server_image: str
    cloud_run_service_name: str


T = TypeVar("T", bound="EdgeState")


@deserialize
@serialize
@dataclass
class EdgeConfig:
    google_cloud_project: GCProjectConfig
    storage_bucket: StorageBucketConfig
    sacred: Optional[SacredConfig] = None
    vertex: Optional[VertexConfig] = None
    web_app: Optional[WebAppConfig] = None

    def save(self, path: str):
        with open(path, "w") as f:
            f.write(to_yaml(self))

    @classmethod
    def load(cls: Type[T], path: str) -> T:
        with open(path) as f:
            yaml_str = "\n".join(f.readlines())

        return from_yaml(EdgeConfig, yaml_str)

    @classmethod
    def load_default(cls: Type[T]) -> T:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../edge.yaml")
        return EdgeConfig.load(config_path)
