from dataclasses import dataclass, field
from typing import TypeVar, Type, Optional, Dict
from serde import serialize, deserialize
from serde.yaml import from_yaml, to_yaml
import os
from contextlib import contextmanager

from edge.tui import StepTUI, SubStepTUI


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
class ModelConfig:
    name: str
    prediction_server_image: str
    endpoint_name: str


@deserialize
@serialize
@dataclass
class WebAppConfig:
    webapp_server_image: str
    cloud_run_service_name: str


T = TypeVar("T", bound="EdgeConfig")


@deserialize
@serialize
@dataclass
class EdgeConfig:
    google_cloud_project: GCProjectConfig
    storage_bucket: StorageBucketConfig
    experiments: Optional[SacredConfig] = None
    models: Dict[str, ModelConfig] = field(default_factory=dict)
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
        config = EdgeConfig.load(config_path)
        return config

    @classmethod
    @contextmanager
    def context(cls: Type[T], to_save: bool = False, silent: bool = False) -> T:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../edge.yaml")
        config = EdgeConfig.load(config_path)
        try:
            yield config
        finally:
            if to_save:
                with StepTUI("Saving vertex:edge configuration", emoji="💾", silent=silent):
                    with SubStepTUI("Saving vertex:edge configuration", silent=silent):
                        config.save(config_path)
