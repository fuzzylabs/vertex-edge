import json
from google.cloud.aiplatform import Model, Endpoint
from edge.config import EdgeConfig
from edge.state import EdgeState

config = EdgeConfig.load_default()
state = EdgeState.load(config)

endpoint = Endpoint(endpoint_name=state.vertex_endpoint_state.endpoint_resource_name)

endpoint.undeploy_all()

with open("../../fashion/vertex_model.json") as f:
    model_dict = json.load(f)

model = Model(model_dict["model_name"])

print("Deploying model")

endpoint.deploy(
    model=model,
    traffic_percentage=100,
    machine_type="n1-standard-2"
)
