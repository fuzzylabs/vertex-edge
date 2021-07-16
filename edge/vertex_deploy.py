from google.cloud.aiplatform import Model, Endpoint


def vertex_deploy(endpoint_resource_name: str, model_name: str):
    endpoint = Endpoint(endpoint_name=endpoint_resource_name)

    endpoint.undeploy_all()

    model = Model(model_name)

    print("Deploying model")

    endpoint.deploy(
        model=model,
        traffic_percentage=100,
        machine_type="n1-standard-2"
    )
