import os
import subprocess
import time
from dataclasses import dataclass
from serde import serialize, deserialize
from .config import EdgeConfig
from google.cloud import container_v1
from google.cloud.container_v1 import Cluster
from google.api_core.exceptions import NotFound
from google.cloud import secretmanager_v1


@deserialize
@serialize
@dataclass
class SacredOutputs:
    internal_mongo_string: str
    external_mongo_string: str
    external_omniboard_string: str


def create_cluster(project_id: str, region: str, cluster_name: str) -> Cluster:
    print("## Creating cluster")
    print(f"Checking if '{cluster_name}' cluster exists")
    client = container_v1.ClusterManagerClient()
    try:
        cluster = client.get_cluster(
            project_id=project_id,
            name=f"projects/{project_id}/locations/{region}/clusters/{cluster_name}"
        )
    except NotFound:
        print(f"Cluster '{cluster_name}' does not exist, creating...")
        os.system(
            f"gcloud container clusters create-auto {cluster_name} --project {project_id} --region {region}"
        )
        cluster = client.get_cluster(
            project_id=project_id,
            name=f"projects/{project_id}/locations/{region}/clusters/{cluster_name}"
        )
        return cluster
    print(f"Cluster '{cluster_name}' exists")
    return cluster


def get_credentials(project_id: str, region: str, cluster_name: str):
    os.system(
        f"gcloud container clusters get-credentials {cluster_name} --project {project_id} --region {region}"
    )


def get_mongodb_password():
    return subprocess.check_output(
        "kubectl get secret --namespace default mongodb -o jsonpath=\"{.data.mongodb-password}\" | base64 --decode",
        shell=True
    ).decode("utf-8")


def get_lb_ip(name):
    return subprocess.check_output(
        f"kubectl get service --namespace default {name} -o jsonpath=\"{{.status.loadBalancer.ingress[0].ip}}\"",
        shell=True
    ).decode("utf-8")


def install_mongodb() -> (str, str):
    print("## Installing MongoDB")
    os.system('''
        helm repo add bitnami https://charts.bitnami.com/bitnami
        helm upgrade -i --wait mongodb bitnami/mongodb --set auth.username=sacred,auth.database=sacred
        kubectl expose deployment mongodb --name mongodb-lb --type LoadBalancer --port 60000 --target-port 27017
    ''')

    password = get_mongodb_password()

    external_ip = get_lb_ip("mongodb-lb")
    while external_ip == "":
        print("Waiting for MongoDB LoadBalancer IP (5 seconds)")
        time.sleep(5)
        external_ip = get_lb_ip("mongodb-lb")

    internal_connection_string = f"mongodb://sacred:{password}@mongodb/sacred"
    external_connection_string = f"mongodb://sacred:{password}@{external_ip}:60000/sacred"

    os.system(
        "kubectl delete secret mongodb-connection; "
        f"kubectl create secret generic mongodb-connection --from-literal=internal={internal_connection_string}"
    )

    print("MongoDB has been installed.")
    print("Internal connection string: ", internal_connection_string)
    print("External connection string: ", external_connection_string)

    return internal_connection_string, external_connection_string


def install_omniboard() -> str:
    print("## Installing Omniboard")
    os.system("kubectl apply -f edge/k8s/omniboard.yaml")

    external_ip = get_lb_ip("omniboard-lb")
    while external_ip == "":
        print("Waiting for Omniboard LoadBalancer IP (5 seconds)")
        time.sleep(5)
        external_ip = get_lb_ip("omniboard-lb")

    print(f"Omniboard is installed and available at http://{external_ip}:9000")

    return f"http://{external_ip}:9000"


def save_mongo_to_secretmanager(_config: EdgeConfig, connection_string: str):
    project_id = _config.google_cloud_project.project_id
    secret_id = _config.sacred.mongodb_connection_string_secret
    print("## Adding MongoDB connection string to Google Cloud Secret Manager")
    client = secretmanager_v1.SecretManagerServiceClient()
    try:
        client.access_secret_version(
            name=f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        )
    except NotFound:
        print(f"Creating '{secret_id}' secret")
        client.create_secret(
            request={
                "parent": f"projects/{project_id}",
                "secret_id": secret_id,
                "secret": {"replication": {"automatic": {}}},
            }
        )

    client.add_secret_version(
        request={
            "parent": f"projects/{project_id}/secrets/{secret_id}",
            "payload": {"data": connection_string.encode()}
        }
    )


def setup_sacred(_config: EdgeConfig):
    print("# Setting up Sacred+Omniboard")

    create_cluster(
        _config.google_cloud_project.project_id,
        _config.google_cloud_project.region,
        _config.sacred.gke_cluster_name
    )

    get_credentials(
        _config.google_cloud_project.project_id,
        _config.google_cloud_project.region,
        _config.sacred.gke_cluster_name
    )

    internal_mongo_string, external_mongo_string = install_mongodb()

    save_mongo_to_secretmanager(_config, external_mongo_string)

    external_omniboard_string = install_omniboard()

    return SacredOutputs(
        internal_mongo_string=internal_mongo_string,
        external_mongo_string=external_mongo_string,
        external_omniboard_string=external_omniboard_string
    )


def get_omniboard(_config: EdgeConfig) -> str:
    get_credentials(
        _config.google_cloud_project.project_id,
        _config.google_cloud_project.region,
        _config.sacred.gke_cluster_name
    )

    return f"http://{get_lb_ip('omniboard-lb')}:9000"
