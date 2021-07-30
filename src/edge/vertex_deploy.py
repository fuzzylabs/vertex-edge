from google.cloud.aiplatform import Model, Endpoint
from google.api_core.exceptions import NotFound

from edge.exception import EdgeException
from edge.tui import StepTUI, SubStepTUI


def vertex_deploy(endpoint_resource_name: str, model_resource_name: str, model_name: str):
    with StepTUI(f"Deploying model '{model_name}'", emoji="🐏"):
        with SubStepTUI(f"Checking endpoint '{endpoint_resource_name}'"):
            try:
                endpoint = Endpoint(endpoint_name=endpoint_resource_name)
            except NotFound:
                raise EdgeException(f"Endpoint '{endpoint_resource_name}' is not found. Please reinitialise the model "
                                    f"by running `./edge.py model init` to create it.")
        with SubStepTUI(f"Undeploying previous models from endpoint '{endpoint_resource_name}'"):
            endpoint.undeploy_all()
        with SubStepTUI(f"Deploying model '{model_resource_name}' on endpoint '{endpoint_resource_name}'"):
            try:
                model = Model(model_resource_name)
            except NotFound:
                raise EdgeException(f"Model '{model_resource_name}' is not found. You need to train a model "
                                    f"by running `dvc repro ...`.")
            endpoint.deploy(model=model, traffic_percentage=100, machine_type="n1-standard-2")
