import argparse
import textwrap
from typing import Optional
from edge.config import *
from edge.state import EdgeState
from edge.sacred import setup_sacred, get_omniboard
from edge.enable_api import enable_api
from edge.endpoint import setup_endpoint
from edge.storage import setup_storage
from serde.yaml import to_yaml, from_yaml


def input_with_default(prompt, default):
    got = input(prompt).strip()
    if got == "":
        got = default
    return got


def create_config(path: str) -> EdgeConfig:
    print("Creating configuration")

    print("Configuring GCP")
    google_cloud_project = GCProjectConfig(
        project_id=input("Google Cloud Project ID: ").strip(),
        region=input("Google Cloud Region: ").strip()
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


def setup_edge(_config: EdgeConfig):
    print("Using configuration")
    print(to_yaml(_config))
    print()

    enable_api(_config)

    storage_bucket_output = setup_storage(_config)

    print("# TODO Setup DVC if not set up")

    sacred_output = setup_sacred(_config)

    vertex_endpoint_output = setup_endpoint(_config)

    output = EdgeState(
        vertex_endpoint_output,
        sacred_output,
        storage_bucket_output,
    )
    print("Setup finished")
    print("Output:")
    print(to_yaml(output))

    with open("edge-output.yaml", "w") as f:
        f.write(to_yaml(output))

    print('''
    The output has been written to `edge-output.yaml`.
    Commit it to git, for others to use.
    
    ```
    git add edge-output.yaml && git commit -m "Add vertex:edge output" && git push
    ```
    ''')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Edge", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
        "command",
        type=str,
        choices=[
            "config",
            "setup",
            "omniboard",
        ],
        help=textwrap.dedent('''\
            Command to run
            config -- create a vertex:edge configuration.
            setup -- setup the project on Google Cloud, according to the configuration 
                     (and create configuration is does not exist), default.
            omniboard -- get Omniboard URL, if it is deployed
            ''')
    )
    parser.add_argument(
        "-c", "--config",
        type=str,
        default="edge.yaml",
        help="Path to the configuration file (default: edge.yaml)"
    )

    args = parser.parse_args()
    print(args)

    if args.command == "config":
        create_config(args.config)
    elif args.command == "setup":
        config = load_config(args.config)
        if config is None:
            print("Configuration, does not exist creating...")
            config = create_config(args.config)
        else:
            print("Configuration is found")
        setup_edge(config)
    elif args.command == "omniboard":
        config = load_config(args.config)
        print(f"Omniboard: {get_omniboard(config)}")
