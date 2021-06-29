from dataclasses import dataclass
from serde import serialize, deserialize


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
    prediction_server_image: str


@deserialize
@serialize
@dataclass
class WebAppConfig:
    webapp_server_image: str
    cloud_run_service_name: str


@deserialize
@serialize
@dataclass
class EdgeConfig:
    google_cloud_project: GCProjectConfig
    storage_bucket: StorageBucketConfig
    sacred: SacredConfig
    vertex: VertexConfig
    web_app: WebAppConfig
