from typing import Optional
from google.cloud import aiplatform
from .config import EdgeConfig
from .state import VertexEndpointState, EdgeState


def get_endpoint(project_id: str, region: str, endpoint_name: str) -> Optional[str]:
    print(f"## Checking if {endpoint_name} endpoint exists")
    endpoints = aiplatform.Endpoint.list(
        filter=f'display_name="{endpoint_name}"',
        project=project_id,
        location=region,
    )
    if len(endpoints) > 1:
        print(f"WARNING: multiple endpoints with {endpoint_name} name were found, using the first found")
    elif len(endpoints) == 0:
        return None
    return endpoints[0].resource_name


def create_endpoint(project_id: str, region: str, endpoint_name: str) -> str:
    print(f"## Creating {endpoint_name} endpoint")
    endpoint = aiplatform.Endpoint.create(
        display_name=endpoint_name,
        project=project_id,
        location=region
    )

    print(f"Endpoint created: {endpoint.resource_name}")
    return endpoint.resource_name


def setup_endpoint(_config: EdgeConfig) -> VertexEndpointState:
    print("# Setting up Vertex AI endpoint")
    endpoint_name = f"{_config.vertex.model_name}-endpoint"
    endpoint_resource_name = get_endpoint(
        _config.google_cloud_project.project_id,
        _config.google_cloud_project.region,
        endpoint_name
    )
    if endpoint_resource_name is None:
        print(f"{endpoint_name} endpoint does not exist")
        endpoint_resource_name = create_endpoint(
            _config.google_cloud_project.project_id,
            _config.google_cloud_project.region,
            endpoint_name
        )
    else:
        print(f"{endpoint_name} endpoint exists: {endpoint_resource_name}")
    return VertexEndpointState(endpoint_resource_name)


def tear_down_endpoint(_config: EdgeConfig, _state: EdgeState):
    print(f"# Tearing down Vertex AI endpoint: {_state.vertex_endpoint_state.endpoint_resource_name}")

    endpoint = aiplatform.Endpoint(_state.vertex_endpoint_state.endpoint_resource_name)
    endpoint.undeploy_all()
    endpoint.delete()
