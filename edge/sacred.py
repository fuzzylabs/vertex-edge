import json
import os
import subprocess
import time
from edge.config import EdgeConfig
from google.cloud import container_v1
from google.cloud.container_v1 import Cluster
from google.api_core.exceptions import NotFound
from google.cloud import secretmanager_v1
from edge.state import SacredState, EdgeState
from sacred.observers import MongoObserver


def create_cluster(project_id: str, region: str, cluster_name: str) -> Cluster:
    print("## Creating Kubernetes cluster on GKE")
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
    try:
        subprocess.check_output(
            f"gcloud container clusters get-credentials {cluster_name} --project {project_id} --region {region}",
            shell=True
        )
    except subprocess.CalledProcessError as e:
        print(e.output)
        print("Error occurred while getting kubernetes cluster credentials")
        exit(1)


def get_mongodb_password():
    try:
        return subprocess.check_output(
            "kubectl get secret --namespace default mongodb -o jsonpath=\"{.data.mongodb-password}\" | base64 --decode",
            shell=True
        ).decode("utf-8")
    except subprocess.CalledProcessError as e:
        print(e.output)
        print("Error occurred while getting MongoDB password")
        exit(1)


def get_lb_ip(name):
    try:
        return subprocess.check_output(
            f"kubectl get service --namespace default {name} -o jsonpath=\"{{.status.loadBalancer.ingress[0].ip}}\"",
            shell=True
        ).decode("utf-8")
    except subprocess.CalledProcessError as e:
        print(e.output)
        print(f"Error occurred while getting IP for {name}")
        exit(1)


def check_mongodb_installed() -> bool:
    helm_charts = json.loads(subprocess.check_output("helm list -o json", shell=True).decode("utf-8"))
    for chart in helm_charts:
        if chart["name"] == "mongodb":
            return True
    return False


def check_mongodb_lb_installed() -> bool:
    try:
        subprocess.check_output(
            "kubectl get service mongodb-lb -o json",
            stderr=subprocess.STDOUT,
            shell=True
        )
    except subprocess.CalledProcessError as e:
        if e.output.decode("utf-8") == "Error from server (NotFound): services \"mongodb-lb\" not found\n":
            return False
        else:
            raise e
    return True


def install_mongodb() -> (str, str):
    try:
        print("## Installing MongoDB")
        if check_mongodb_installed():
            print("MongoDB is already installed")
        else:
            subprocess.check_output('''
                helm repo add bitnami https://charts.bitnami.com/bitnami
                helm upgrade -i --wait mongodb bitnami/mongodb --set auth.username=sacred,auth.database=sacred
            ''', shell=True)

        print("## Exposing MongoDB")
        if check_mongodb_lb_installed():
            print("MongoDB is already exposed")
        else:
            subprocess.check_output('''
                kubectl expose deployment mongodb --name mongodb-lb --type LoadBalancer --port 60000 --target-port 27017
            ''', shell=True)
    except subprocess.CalledProcessError as e:
        print(e.output)
        print("Error occurred while installing MongoDB with helm chart")
        exit(1)

    password = get_mongodb_password()

    external_ip = get_lb_ip("mongodb-lb")
    while external_ip == "":
        print("Waiting for MongoDB LoadBalancer IP (5 seconds)")
        time.sleep(5)
        external_ip = get_lb_ip("mongodb-lb")

    internal_connection_string = f"mongodb://sacred:{password}@mongodb/sacred"
    external_connection_string = f"mongodb://sacred:{password}@{external_ip}:60000/sacred"

    try:
        output = subprocess.check_output(
            "kubectl delete secret mongodb-connection",
            shell=True,
            stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError as exc:
        if "NotFound" in exc.output.decode("utf-8"):
            pass  # error expected if the secret was not previously created
        else:
            print(exc.output.decode("utf-8"))
            print("Error while trying to delete mongodb-connection secret")
    else:
        print(output.decode("utf-8").strip())
    os.system(
        f"kubectl create secret generic mongodb-connection --from-literal=internal={internal_connection_string}"
    )

    print("MongoDB has been installed.")
    print("Internal connection string: ", f"mongodb://sacred:*****@mongodb/sacred")
    print("External connection string: ", f"mongodb://sacred:*****@{external_ip}:60000/sacred")

    return internal_connection_string, external_connection_string


def install_omniboard() -> str:
    print("## Installing Omniboard (Web UI)")
    try:
        subprocess.check_output("kubectl apply -f edge/k8s/omniboard.yaml", shell=True)
    except subprocess.CalledProcessError as e:
        print(e.output)
        print("Error occurred while applying Omniboard's configuration")
        exit(1)

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


def delete_mongo_to_secretmanager(_config: EdgeConfig):
    project_id = _config.google_cloud_project.project_id
    secret_id = _config.sacred.mongodb_connection_string_secret
    print("## Removing MongoDB connection string from Google Cloud Secret Manager")
    client = secretmanager_v1.SecretManagerServiceClient()

    try:
        client.access_secret_version(
            name=f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        )
        client.delete_secret(name=f"projects/{project_id}/secrets/{secret_id}")
    except NotFound:
        print("Secret does not exist")
        return


def delete_cluster(_config: EdgeConfig):
    project_id = _config.google_cloud_project.project_id
    region = _config.google_cloud_project.region
    cluster_name = _config.sacred.gke_cluster_name
    print(f"## Deleting cluster '{cluster_name}'")
    client = container_v1.ClusterManagerClient()
    try:
        client.get_cluster(
            project_id=project_id,
            name=f"projects/{project_id}/locations/{region}/clusters/{cluster_name}"
        )
        os.system(
            f"gcloud container clusters delete {cluster_name} --project {project_id} --region {region}"
        )
    except NotFound:
        print("Cluster does not exist")


def setup_sacred(_config: EdgeConfig):
    print("# Setting up MongoDB for experiment tracking (Sacred and Omniboard)")

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

    return SacredState(
        external_omniboard_string=external_omniboard_string
    )


def tear_down_sacred(_config: EdgeConfig, _state: EdgeState):
    print("# Tearing down Sacred+Omniboard")

    delete_mongo_to_secretmanager(_config)
    delete_cluster(_config)


def get_omniboard(_config: EdgeConfig) -> str:
    get_credentials(
        _config.google_cloud_project.project_id,
        _config.google_cloud_project.region,
        _config.sacred.gke_cluster_name
    )

    return f"http://{get_lb_ip('omniboard-lb')}:9000"


def get_mongo_observer(config: EdgeConfig) -> MongoObserver:
    client = secretmanager_v1.SecretManagerServiceClient()

    project_id = config.google_cloud_project.project_id
    secret_id = config.sacred.mongodb_connection_string_secret
    secret_name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(name=secret_name)

    mongo_connection_string = response.payload.data.decode('UTF-8')
    return MongoObserver(mongo_connection_string)
