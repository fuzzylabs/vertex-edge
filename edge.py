#!/usr/bin/env python
"""
vertex:edge CLI tool
"""
import argparse
import json
import os
import subprocess
import sys
import time
from typing import Optional
from serde.yaml import to_yaml, from_yaml

from edge.command.init import edge_init
from edge.command.dvc.subparser import add_dvc_parser, run_dvc_actions
from edge.command.model.subparser import add_model_parser, run_model_actions
from edge.config import EdgeConfig, GCProjectConfig, ModelConfig, SacredConfig, StorageBucketConfig, WebAppConfig
from edge.state import EdgeState
from edge.sacred import setup_sacred, tear_down_sacred
from edge.enable_api import enable_api, enable_service_api
from edge.endpoint import setup_endpoint, tear_down_endpoint
from edge.storage import setup_storage, tear_down_storage
from edge.dvc import setup_dvc
from edge.vertex_deploy import vertex_deploy
from edge.gcloud import (
    get_gcp_regions, get_gcloud_region, get_gcloud_project, get_gcloud_account, is_billing_enabled, is_authenticated,
    project_exists
)
from edge.tui import (
    print_substep, print_heading, print_step, print_substep_not_done, print_substep_success, print_substep_failure,
    print_failure_explanation, clear_last_line, qmark, print_substep_warning, print_warning_explanation, SubStepTUI,
    TUIStatus, TUI, StepTUI
)
from edge.versions import get_kubectl_version, get_gcloud_version, get_helm_version, Version
from edge.exception import EdgeException
import atexit
import warnings
import questionary
import logging

logging.disable(logging.WARNING)
warnings.filterwarnings(
    "ignore",
    "Your application has authenticated using end user credentials from Google Cloud SDK without a quota project.",
)

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
    return True


def get_valid_gcp_region(project: str):
    _regions = get_gcp_regions(project)
    _region = ""
    while _region not in _regions:
        _region = input("Google Cloud Region: ").strip()
        if _region not in _regions:
            print(f"{_region} is not a region that is available in Vertex AI. Choose one of the regions below:")
            print("\n".join([f"\t{x}" for x in _regions]))
    return _region


def create_config(path: str) -> EdgeConfig:
    print("Creating configuration")

    print("Configuring GCP")
    project_id = input("Google Cloud Project ID: ").strip()
    region = get_valid_gcp_region(project_id)
    google_cloud_project = GCProjectConfig(project_id=project_id, region=region)

    print()
    print("Configuring Vertex AI")
    model_name = input("Model name: ").strip()
    vertex = ModelConfig(
        model_name=model_name,
        prediction_server_image=input_with_default(
            f"Vertex AI prediction server image [{model_name}-prediction]: ", f"{model_name}-prediction"
        ),
    )

    print()
    print("Configuring Storage Bucket")
    storage_bucket = StorageBucketConfig(
        bucket_name=input_with_default(f"Storage bucket name [{vertex.name}-model]: ", f"{model_name}-model"),
        dvc_store_directory=input_with_default("DVC store directory within the bucket [dvcstore]: ", "dvcstore"),
        vertex_jobs_directory=input_with_default("Vertex AI jobs directory within the bucket [vertex]: ", "vertex"),
    )

    print()
    print("Configuring Sacred")
    sacred = SacredConfig(
        gke_cluster_name=input_with_default("Sacred GKE cluster name [sacred]: ", "sacred"),
        mongodb_connection_string_secret=input_with_default(
            "MongoDB connection string secret name [sacred-mongodb-connection-string]: ",
            "sacred-mongodb-connection-string",
        ),
    )

    print()
    print("Configuring web app")
    web_app = WebAppConfig(
        webapp_server_image=input_with_default(f"Web app server image [{model_name}-webapp]: ", f"{model_name}-webapp"),
        cloud_run_service_name=input_with_default(
            f"Cloud run service name [{model_name}-webapp]: ", f"{model_name}-webapp"
        ),
    )

    print()
    _config = EdgeConfig(google_cloud_project, storage_bucket, sacred, vertex, web_app)
    print("Configuration")
    print(to_yaml(_config))

    with open(path, "w") as file:
        file.write(to_yaml(_config))

    return _config


def load_config(path: str) -> Optional[EdgeConfig]:
    try:
        with open(path) as file:
            yaml_str = "\n".join(file.readlines())
    except FileNotFoundError:
        return None

    try:
        _config = from_yaml(EdgeConfig, yaml_str)
    except KeyError:
        print("Configuration file is malformed")
        sys.exit(1)

    return _config


def setup_edge(_config: EdgeConfig, _lock_later: bool):
    print("Using configuration")
    print(to_yaml(_config))
    print()

    enable_api(_config)
    print()

    # storage_bucket_output = setup_storage(_config)
    # if _lock_later:
    #     EdgeState.lock(config.google_cloud_project.project_id, config.storage_bucket.bucket_name)
    print()

    # setup_dvc(_config, storage_bucket_output)
    # print()

    sacred_output = setup_sacred(_config)
    print()

    vertex_endpoint_output = setup_endpoint(_config)
    print()

    _state = EdgeState(
        vertex_endpoint_output,
        sacred_output,
        # storage_bucket_output,
    )
    _state.save(_config)

    print()
    print("Setup finished")
    print("Resulting state (saved to Google Storage):")
    print(to_yaml(_state))


def tear_down_edge(_config: EdgeConfig, _state: EdgeState):
    print("WARNING: The following operations are destructive")

    keep_state = False

    if _state.vertex_endpoint_state is not None:
        if input_yn(
            f"Do you want to destroy Vertex AI endpoint: {_state.vertex_endpoint_state.endpoint_resource_name}", "n"
        ):
            tear_down_endpoint(_config, _state)
            _state.vertex_endpoint_state = None
        else:
            print("Vertex AI endpoint is kept")
        print()

    if _state.sacred_state is not None:
        if input_yn(
            f"Do you want to destroy experiment tracker Kubernetes cluster (MongoDB+Omniboard): "
            f"{_config.sacred.gke_cluster_name}",
            "n",
        ):
            tear_down_sacred(_config, _state)
            _state.sacred_state = None
        else:
            print("Sacred cluster is kept")
        print()

    if _state.storage is not None:
        if input_yn(f"Do you want to destroy Google Storage bucket: {_config.storage_bucket.bucket_name}", "n"):
            tear_down_storage(_config, _state)
            _state.storage = None
        else:
            keep_state = True
            print("Storage bucket is kept")
        print()

    if is_cloud_run_deployed(_config):
        if input_yn(f"Do you want to stop Cloud Run service: {_config.web_app.cloud_run_service_name}", "n"):
            print("# Cloud Run service is stopping...")
            remove_cloud_run(_config)
        else:
            print("Cloud Run service is kept")
        print()

    if keep_state:
        print("Google Storage bucket is still present, so the state is kept")
        _state.save(_config)
        print(to_yaml(state))
        EdgeState.unlock(_config.google_cloud_project.project_id, _config.storage_bucket.bucket_name)
    sys.exit(0)


def deploy_cloud_run(_config: EdgeConfig, _state: EdgeState, tag: str):
    subprocess.run(
        f"gcloud run deploy {_config.web_app.cloud_run_service_name} \
        --image gcr.io/{_config.google_cloud_project.project_id}/{_config.web_app.webapp_server_image}:{tag} \
        --set-env-vars ENDPOINT_ID={_state.vertex_endpoint_state.endpoint_resource_name} \
        --platform managed --allow-unauthenticated \
        --project {_config.google_cloud_project.project_id} --region {_config.google_cloud_project.region}",
        shell=True,
        env=os.environ.copy(),
    )


def remove_cloud_run(_config: EdgeConfig):
    subprocess.run(
        f"gcloud run services delete {_config.web_app.cloud_run_service_name} \
        --platform managed \
        --project {_config.google_cloud_project.project_id} --region {_config.google_cloud_project.region}",
        shell=True,
        env=os.environ.copy(),
    )


def is_cloud_run_deployed(_config: EdgeConfig) -> bool:
    services = json.loads(
        subprocess.check_output(
            f"gcloud run services list --platform managed --format json \
        --project {_config.google_cloud_project.project_id} --region {_config.google_cloud_project.region}",
            shell=True,
            env=os.environ.copy(),
        ).decode("utf-8")
    )
    for service in services:
        if service["metadata"]["name"] == _config.web_app.cloud_run_service_name:
            return True
    return False


def vertex_deploy_from_state(_state: EdgeState):
    with open("models/fashion/vertex_model.json") as file:
        model_dict = json.load(file)

    vertex_deploy(_state.vertex_endpoint_state.endpoint_resource_name, model_dict["model_name"])


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
        f"{image_name}:{tag}"
    )


def safe_exit(_config: EdgeConfig, _state: Optional[EdgeState]):
    EdgeState.unlock(config.google_cloud_project.project_id, config.storage_bucket.bucket_name)


def acquire_state(_config: EdgeConfig) -> (Optional[EdgeState], bool):
    _state_locked, _lock_later = EdgeState.lock(
        config.google_cloud_project.project_id,
        config.storage_bucket.bucket_name
    )
    if not _state_locked and not _lock_later:
        print("Cannot lock state, exiting...")
        sys.exit(1)
    _state = EdgeState.load(config)
    atexit.register(safe_exit, config, _state)
    return _state, _lock_later


def vertex_handler(_config, _args):
    if _args.action == "build-docker":
        tag = os.environ.get("TAG") or "latest"
        path = "models/fashion"
        image_name = f"gcr.io/{_config.google_cloud_project.project_id}/{_config.vertex.prediction_server_image}"
        build_docker(path, image_name, tag)
        push_docker(image_name, tag)
        sys.exit(0)
    elif _args.action == "get-endpoint":
        _state, _ = acquire_state(_config)
        if _state is None or _state.vertex_endpoint_state is None:
            print("Vertex AI endpoint is not deployed, run `./edge.py install` to deploy it")
        else:
            print(f"{_state.vertex_endpoint_state.endpoint_resource_name}")
        sys.exit(0)
    elif _args.action == "deploy":
        _state, _ = acquire_state(_config)
        if _state is None or _state.vertex_endpoint_state is None:
            print("Vertex AI endpoint is not deployed, run `./edge.py install` to deploy it")
        else:
            vertex_deploy_from_state(_state)
        sys.exit(0)


def webapp_handler(_config, _args):
    if _args.action == "build-docker":
        tag = os.environ.get("TAG") or "latest"
        path = "services/fashion-web"
        image_name = f"gcr.io/{_config.google_cloud_project.project_id}/{_config.web_app.webapp_server_image}"
        build_docker(path, image_name, tag)
        push_docker(image_name, tag)
        sys.exit(0)
    elif _args.action == "run":
        tag = os.environ.get("TAG") or "latest"
        _state = EdgeState.load(config)
        path = "services/fashion-web"
        image_name = f"gcr.io/{config.google_cloud_project.project_id}/{config.web_app.webapp_server_image}"
        build_docker(path, image_name, tag)
        run_docker_service(_state.vertex_endpoint_state.endpoint_resource_name, image_name, tag)
        sys.exit(0)
    elif _args.action == "deploy":
        _state, _ = acquire_state(_config)
        tag = os.environ.get("TAG") or "latest"
        deploy_cloud_run(config, _state, tag)
        sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Edge", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
        "-c", "--config", type=str, default="edge.yaml", help="Path to the configuration file (default: edge.yaml)"
    )

    subparsers = parser.add_subparsers(title="command", dest="command", required=True)
    init_parser = subparsers.add_parser("init")

    add_dvc_parser(subparsers)
    add_model_parser(subparsers)

    # config_parser = subparsers.add_parser("config", help="Run configuration wizard")
    # install_parser = subparsers.add_parser(
    #     "install", help="Setup the project on Google Cloud, according to the configuration"
    # )
    # force_unlock_parser = subparsers.add_parser("force-unlock", help="Unlock state file explicitly")
    # uninstall_parser = subparsers.add_parser(
    #     "uninstall", help="Tear down Google Cloud infrastructure associated with this project (WARNING: DESTRUCTIVE)"
    # )
    # omniboard_parser = subparsers.add_parser("omniboard", help="Get Omniboard URL, if it is deployed")
    #
    # vertex_parser = subparsers.add_parser("vertex", help="Vertex AI related actions")
    # vertex_subparsers = vertex_parser.add_subparsers(title="action", dest="action", required=True)
    # vertex_subparsers.add_parser("get-endpoint", help="Get Vertex AI endpoint resource name")
    # vertex_subparsers.add_parser(
    #     "build-docker", help="Build Docker container for the prediction server and push it to Google Container Registry"
    # )
    # vertex_subparsers.add_parser("deploy", help="Deploy the trained model to Vertex AI")
    #
    # webapp_parser = subparsers.add_parser("webapp", help="Webapp related actions")
    # webapp_subparsers = webapp_parser.add_subparsers(title="action", dest="action", required=True)
    # webapp_subparsers.add_parser("run", help="Run the webapp locally in Docker")
    # webapp_subparsers.add_parser(
    #     "build-docker", help="Build Docker container for the webapp and push it to Google Container Registry"
    # )
    # webapp_subparsers.add_parser("deploy", help="Deploy the webapp to Cloud Run")

    args = parser.parse_args()

    # Init does not require config or state
    if args.command == "init":
        edge_init()
    elif args.command == "dvc":
        run_dvc_actions(args)
    elif args.command == "model":
        run_model_actions(args)

    raise NotImplementedError("The rest of the commands are not implemented")
    # Load configuration, and state (if exist) and lock state
    # print("Loading configuration...")
    # config = load_config(args.config)
    # if config is None:
    #     print("Configuration, does not exist creating...")
    #     config = create_config(args.config)
    # else:
    #     print("Configuration is found")
    #
    # if args.command == "force-unlock":
    #     EdgeState.unlock(config.google_cloud_project.project_id, config.storage_bucket.bucket_name)
    #     sys.exit(0)
    #
    # # Commands with subactions
    # if args.command == "vertex":
    #     vertex_handler(config, args)
    # elif args.command == "webapp":
    #     webapp_handler(config, args)
    #
    # # Commands that do not require state lock
    # if args.command == "config":
    #     create_config(args.config)
    #     sys.exit(0)
    #
    # # Command that require state and should lock it
    # state, lock_later = acquire_state(config)
    # if args.command == "install":
    #     setup_edge(config, lock_later)
    #     sys.exit(0)
    # elif args.command == "omniboard":
    #     if state is None or state.sacred_state is None:
    #         print("Omniboard is not deployed")
    #     else:
    #         print(f"Omniboard: {state.sacred_state.external_omniboard_string}")
    #     sys.exit(0)
    # elif args.command == "uninstall":
    #     if state is None:
    #         print("Vertex:Edge state does not exist, nothing to uninstall.")
    #     else:
    #         tear_down_edge(config, state)
    #     sys.exit(0)
    # else:
    #     raise Exception(f"{args.command} command is not supported")
