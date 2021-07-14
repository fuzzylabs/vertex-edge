import argparse
import json
import os
import subprocess
import textwrap
from typing import Optional
from edge.config import *
from edge.state import EdgeState
from edge.sacred import setup_sacred, get_omniboard, tear_down_sacred
from edge.enable_api import enable_api
from edge.endpoint import setup_endpoint, tear_down_endpoint
from edge.storage import setup_storage, tear_down_storage
from edge.dvc import setup_dvc
from serde.yaml import to_yaml, from_yaml
from edge.vertex_deploy import vertex_deploy
from edge.gcloud import get_gcp_regions
import atexit

config = None
state = None
state_locked = False
lock_later = False


def input_with_default(prompt, default):
    got = input(prompt).strip()
    if got == "":
        got = default
    return got


def input_yn(promt, default) -> bool:
    choice = None
    while choice not in ["y", "n"]:
        choice = input(f"{promt} (y/n)? [{default}]: ").strip().lower()
        if choice == "":
            choice = default

    if choice == "n":
        return False
    else:
        return True


def get_valid_gcp_region(project: str):
    regions = get_gcp_regions(project)
    region = ""
    while region not in regions:
        region = input("Google Cloud Region: ").strip()
        if region not in regions:
            print(f"{region} is not a valid region")
    return region


def create_config(path: str) -> EdgeConfig:
    print("Creating configuration")

    print("Configuring GCP")
    project_id = input("Google Cloud Project ID: ").strip()
    region = get_valid_gcp_region(project_id)
    google_cloud_project = GCProjectConfig(
        project_id=project_id,
        region=region
    )

    print()
    print("Configuring Vertex AI")
    model_name = input("Model name: ").strip()
    vertex = VertexConfig(
        model_name=model_name,
        prediction_server_image=input_with_default(
            f"Vertex AI prediction server image [{model_name}-prediction]: ",
            f"{model_name}-prediction"
        ),
    )

    print()
    print("Configuring Storage Bucket")
    storage_bucket = StorageBucketConfig(
        bucket_name=input_with_default(f"Storage bucket name [{vertex.model_name}-model]: ", f"{model_name}-model"),
        dvc_store_directory=input_with_default("DVC store directory [dvcstore]: ", "dvcstore"),
        vertex_jobs_directory=input_with_default("Vertex AI jobs directory [vertex]: ", "vertex")
    )

    print()
    print("Configuring Sacred")
    sacred = SacredConfig(
        gke_cluster_name=input_with_default("Sacred GKE cluster name [sacred]: ", "sacred"),
        mongodb_connection_string_secret=input_with_default(
            "MongoDB connection string secret name [sacred-mongodb-connection-string]: ",
            "sacred-mongodb-connection-string"
        ),
    )

    print()
    print("Configuring web app")
    web_app = WebAppConfig(
        webapp_server_image=input_with_default(f"Web app server image [{model_name}-webapp]: ", f"{model_name}-webapp"),
        cloud_run_service_name=input_with_default(
            f"Cloud run service name [{model_name}-webapp]: ",
            f"{model_name}-webapp"
        )
    )

    print()
    _config = EdgeConfig(
        google_cloud_project,
        storage_bucket,
        sacred,
        vertex,
        web_app
    )
    print("Configuration")
    print(to_yaml(_config))

    with open(path, "w") as f:
        f.write(to_yaml(_config))

    return _config


def load_config(path: str) -> Optional[EdgeConfig]:
    try:
        with open(path) as f:
            yaml_str = "\n".join(f.readlines())
    except FileNotFoundError:
        return None

    try:
        _config = from_yaml(EdgeConfig, yaml_str)
    except KeyError:
        print("Configuration file is malformed")
        exit(1)
        return None

    return _config


def setup_edge(_config: EdgeConfig, lock_later: bool):
    print("Using configuration")
    print(to_yaml(_config))
    print()

    enable_api(_config)

    storage_bucket_output = setup_storage(_config)
    if lock_later:
        EdgeState.lock(
            config.google_cloud_project.project_id,
            config.storage_bucket.bucket_name
        )

    setup_dvc(_config, storage_bucket_output)

    sacred_output = setup_sacred(_config)

    vertex_endpoint_output = setup_endpoint(_config)

    state = EdgeState(
        vertex_endpoint_output,
        sacred_output,
        storage_bucket_output,
    )
    state.save(_config)

    print()
    print("Setup finished")
    print("Resulting state (saved to Google Storage):")
    print(to_yaml(state))


def tear_down_edge(_config: EdgeConfig, _state: EdgeState):
    print("WARNING: The following operations are destructive")

    keep_state = False

    if _state.vertex_endpoint_state is not None:
        if input_yn(
                f"Do you want to destroy Vertex AI endpoint: {_state.vertex_endpoint_state.endpoint_resource_name}",
                "n"
        ):
            tear_down_endpoint(_config, _state)
            _state.vertex_endpoint_state = None
        else:
            print("Vertex AI endpoint is kept")

    if _state.sacred_state is not None:
        if input_yn(f"Do you want to destroy Sacred GKE cluster: {_config.sacred.gke_cluster_name}", "n"):
            tear_down_sacred(_config, _state)
            _state.sacred_state = None
        else:
            print("Sacred cluster is kept")

    if _state.storage_bucket_state is not None:
        if input_yn(f"Do you want to destroy Google Storage bucket: {_config.storage_bucket.bucket_name}", "n"):
            tear_down_storage(_config, _state)
            _state.storage_bucket_state = None
        else:
            keep_state = True
            print("Storage bucket is kept")

    if is_cloud_run_deployed(_config):
        if input_yn(f"Do you want to stop Cloud Run service: {_config.web_app.cloud_run_service_name}", "n"):
            print("# Cloud Run service is stopping...")
            remove_cloud_run(_config)
        else:
            print("Cloud Run service is kept")

    if keep_state:
        print("Google Storage bucket is still present, so the state is kept")
        _state.save(_config)
        print(to_yaml(state))
        EdgeState.unlock(
            _config.google_cloud_project.project_id,
            _config.storage_bucket.bucket_name
        )
    exit(0)


def build_docker(docker_path, image_name, tag="latest"):
    os.system(
        f"docker build -t {image_name}:{tag} {docker_path}"
    )


def push_docker(image_name, tag="latest"):
    os.system(
        f"docker push {image_name}:{tag}"
    )


def deploy_cloud_run(_config: EdgeConfig, _state: EdgeState, tag: str):
    subprocess.run(
        f"gcloud run deploy {_config.web_app.cloud_run_service_name} \
        --image gcr.io/{_config.google_cloud_project.project_id}/{_config.web_app.webapp_server_image}:{tag} \
        --set-env-vars ENDPOINT_ID={_state.vertex_endpoint_state.endpoint_resource_name} \
        --platform managed --allow-unauthenticated \
        --project {_config.google_cloud_project.project_id} --region {_config.google_cloud_project.region}",
        shell=True,
        env=os.environ.copy()
    )


def remove_cloud_run(_config: EdgeConfig):
    subprocess.run(
        f"gcloud run services delete {_config.web_app.cloud_run_service_name} \
        --platform managed \
        --project {_config.google_cloud_project.project_id} --region {_config.google_cloud_project.region}",
        shell=True,
        env=os.environ.copy()
    )


def is_cloud_run_deployed(_config: EdgeConfig) -> bool:
    services = json.loads(subprocess.check_output(
        f"gcloud run services list --platform managed --format json \
        --project {_config.google_cloud_project.project_id} --region {_config.google_cloud_project.region}",
        shell=True,
        env=os.environ.copy()
    ).decode("utf-8"))
    for service in services:
        if service["metadata"]["name"] == _config.web_app.cloud_run_service_name:
            return True
    return False


def vertex_deploy_from_state(state: EdgeState):
    with open("models/fashion/vertex_model.json") as f:
        model_dict = json.load(f)

    vertex_deploy(
        state.vertex_endpoint_state.endpoint_resource_name,
        model_dict["model_name"]
    )


def get_google_application_credentials():
    credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if credentials_path is None:
        credentials_path = "~/.config/gcloud/application_default_credentials.json"
        print(
            f"WARNING: assuming Google Application Credentials at {credentials_path}, "
            f"set GOOGLE_APPLICATION_CREDENTIALS to override"
        )
    return credentials_path


def run_docker_service(endpoint_id: str, image_name: str, tag: str = "latest"):
    credentials_path = get_google_application_credentials()
    os.system(
        "docker run "
        f"-v {credentials_path}:/key.json "
        "-e GOOGLE_APPLICATION_CREDENTIALS='/key.json' "
        f"-e ENDPOINT_ID='{endpoint_id}' "
        "-it -p 8080:8080 "
        "gcr.io/$PROJECT_ID/fashion-mnist-webapp"
    )


def safe_exit(_config: EdgeConfig, _state: Optional[EdgeState]):
    EdgeState.unlock(
        config.google_cloud_project.project_id,
        config.storage_bucket.bucket_name
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Edge", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
        "command",
        type=str,
        choices=[
            "config",
            "setup",
            "force-unlock",
            "omniboard",
            "vertex-endpoint",
            "vertex-deploy",
            "run-webapp",
            "docker-webapp",
            "docker-vertex-prediction",
            "cloud-run-webapp",
            "tear-down"
        ],
        help=textwrap.dedent('''\
            Command to run:
            config -- create a vertex:edge configuration.
            setup -- setup the project on Google Cloud, according to the configuration 
                     (and create configuration is does not exist), default.
            force-unlock -- unlock state file explicitly
            omniboard -- get Omniboard URL, if it is deployed
            vertex-endpoint -- get Vertex AI endpoint
            vertex-deploy -- deploy the trained model to Vertex AI
            run-webapp -- run the web app locally in Docker
            docker-webapp -- build Docker container for the web app and push it to Google Container Registry
            docker-vertex-prediction -- build Docker container for the prediction server and push it to Google Container Registry
            cloud-run-webapp -- deploy the webapp to cloud run
            tear-down -- tear down Google Cloud infrastructure associated with this project (WARNING DESTRUCTIVE)
            ''')
    )
    parser.add_argument(
        "-c", "--config",
        type=str,
        default="edge.yaml",
        help="Path to the configuration file (default: edge.yaml)"
    )

    args = parser.parse_args()

    # Load configuration, and state (if exist) and lock state
    print("Loading configuration...")
    config = load_config(args.config)
    if config is None:
        print("Configuration, does not exist creating...")
        config = create_config(args.config)
    else:
        print("Configuration is found")
    atexit.register(safe_exit, config, state)

    if args.command == "force-unlock":
        EdgeState.unlock(
            config.google_cloud_project.project_id,
            config.storage_bucket.bucket_name
        )
        exit(0)

    state_locked, lock_later = EdgeState.lock(
        config.google_cloud_project.project_id,
        config.storage_bucket.bucket_name
    )
    if not state_locked and not lock_later:
        print("Cannot lock state, exiting...")
        exit(1)
    state = EdgeState.load(config)
    if args.command == "config":
        create_config(args.config)
    elif args.command == "setup":
        setup_edge(config, lock_later)
    elif args.command == "omniboard":
        state = EdgeState.load(config)
        print(f"Omniboard: {state.sacred_state.external_omniboard_string}")
    elif args.command == "vertex-endpoint":
        state = EdgeState.load(config)
        print(f"{state.vertex_endpoint_state.endpoint_resource_name}")
    elif args.command == "vertex-deploy":
        state = EdgeState.load(config)
        vertex_deploy_from_state(state)
    elif args.command == "docker-vertex-prediction":
        tag = os.environ.get("TAG") or "latest"
        path = "models/pipelines/fashion"
        image_name = f"gcr.io/{config.google_cloud_project.project_id}/{config.vertex.prediction_server_image}"
        build_docker(path, image_name, tag)
        push_docker(image_name, tag)
    elif args.command == "docker-webapp":
        tag = os.environ.get("TAG") or "latest"
        path = "services/fashion-web"
        image_name = f"gcr.io/{config.google_cloud_project.project_id}/{config.web_app.webapp_server_image}"
        build_docker(path, image_name, tag)
        push_docker(image_name, tag)
    elif args.command == "cloud-run-webapp":
        tag = os.environ.get("TAG") or "latest"
        state = EdgeState.load(config)
        deploy_cloud_run(config, state, tag)
    elif args.command == "run-webapp":
        tag = os.environ.get("TAG") or "latest"
        state = EdgeState.load(config)
        path = "services/fashion-web"
        image_name = f"gcr.io/{config.google_cloud_project.project_id}/{config.web_app.webapp_server_image}"
        build_docker(path, image_name, tag)
        run_docker_service(state.vertex_endpoint_state.endpoint_resource_name, image_name, tag)
    elif args.command == "tear-down":
        state = EdgeState.load(config)
        tear_down_edge(config, state)
    else:
        raise Exception(f"{args.command} command is not supported")
