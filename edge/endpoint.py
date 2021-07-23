"""
Performing operations on Vertex AI endpoints
"""
import re
from typing import Optional
from google.cloud import aiplatform
from google.api_core.exceptions import PermissionDenied
from .config import EdgeConfig
from .exception import EdgeException
from .state import ModelState, EdgeState
from .tui import StepTUI, SubStepTUI, TUIStatus


def get_endpoint(sub_step: SubStepTUI, project_id: str, region: str, endpoint_name: str) -> Optional[str]:
    """
    Get Vertex AI endpoint resource name

    :param sub_step:
    :param project_id:
    :param region:
    :param endpoint_name:
    :return:
    """
    endpoints = aiplatform.Endpoint.list(
        filter=f'display_name="{endpoint_name}"',
        project=project_id,
        location=region,
    )
    if len(endpoints) > 1:
        sub_step.update(status=TUIStatus.WARNING)
        sub_step.add_explanation(
            f"Multiple endpoints with '{endpoint_name}' name were found. Vertex:edge will use the first one found"
        )
    elif len(endpoints) == 0:
        return None
    return endpoints[0].resource_name


def create_endpoint(project_id: str, region: str, endpoint_name: str) -> str:
    """
    Create an endpoint on Vertex AI

    :param project_id:
    :param region:
    :param endpoint_name:
    :return:
    """
    try:
        endpoint = aiplatform.Endpoint.create(display_name=endpoint_name, project=project_id, location=region)

        return endpoint.resource_name
    except PermissionDenied as error:
        try:
            permission = re.search("Permission '(.*)' denied", error.args[0]).group(1)
            raise EdgeException(
                f"Endpoint '{endpoint_name}' could not be created in project '{project_id}' "
                f"because you have insufficient permission. Make sure you have '{permission}' permission."
            ) from error
        except AttributeError as attribute_error:
            raise error from attribute_error


def setup_endpoint(project_id: str, region: str, endpoint_name: str) -> ModelState:
    """
    Setup procedure for Vertex AI endpoint

    :param project_id:
    :param region:
    :param endpoint_name:
    :return:
    """
    with StepTUI("Configuring Vertex AI endpoint", emoji="☁️"):
        with SubStepTUI(f"Checking if Vertex AI endpoint '{endpoint_name}' exists") as sub_step:
            endpoint_resource_name = get_endpoint(
                sub_step, project_id, region, endpoint_name
            )
            if endpoint_resource_name is None:
                sub_step.update(message=f"'{endpoint_name}' endpoint does not exist, creating...")
                endpoint_resource_name = create_endpoint(
                    project_id, region, endpoint_name
                )
                sub_step.update(message="Created 'fashion-endpoint' endpoint")
            return ModelState(endpoint_resource_name)


def tear_down_endpoint(_config: EdgeConfig, _state: EdgeState):
    print(f"# Tearing down Vertex AI endpoint: {_state.vertex_endpoint_state.endpoint_resource_name}")

    endpoint = aiplatform.Endpoint(_state.vertex_endpoint_state.endpoint_resource_name)
    endpoint.undeploy_all()
    endpoint.delete()
