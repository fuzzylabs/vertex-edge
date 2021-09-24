import json
import os
import subprocess
import time
from edge.config import EdgeConfig
from google.cloud import container_v1
from google.cloud.container_v1 import Cluster
from google.api_core.exceptions import NotFound, PermissionDenied
from google.cloud import secretmanager_v1

from edge.exception import EdgeException
from edge.state import SacredState, EdgeState
from sacred.observers import MongoObserver
from sacred.experiment import Experiment

from edge.tui import StepTUI, SubStepTUI, TUIStatus


def create_cluster(project_id: str, region: str, cluster_name: str) -> Cluster:
    with SubStepTUI(f"Checking if '{cluster_name}' cluster exists") as sub_step:
        client = container_v1.ClusterManagerClient()
        try:
            cluster = client.get_cluster(
                project_id=project_id, name=f"projects/{project_id}/locations/{region}/clusters/{cluster_name}"
            )
        except NotFound:
            sub_step.update(message=f"Cluster '{cluster_name}' does not exist, creating... (may take a few minutes)")
            try:
                subprocess.check_output(
                    f"gcloud container clusters create-auto {cluster_name} --project {project_id} --region {region}",
                    shell=True, stderr=subprocess.STDOUT
                )
            except subprocess.CalledProcessError as exc:
                raise EdgeException(f"Error occurred while creating cluster '{cluster_name}'\n{exc.output}")

            cluster = client.get_cluster(
                project_id=project_id, name=f"projects/{project_id}/locations/{region}/clusters/{cluster_name}"
            )
            sub_step.update(message=f"Cluster '{cluster_name}' created", status=TUIStatus.SUCCESSFUL)
            return cluster
    return cluster


def get_credentials(project_id: str, region: str, cluster_name: str):
    with SubStepTUI("Getting cluster credentials"):
        try:
            subprocess.check_output(
                f"gcloud container clusters get-credentials {cluster_name} --project {project_id} --region {region}",
                shell=True,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            raise EdgeException(f"Error occurred while getting kubernetes cluster credentials\n{e.output}")


def get_mongodb_password():
    with SubStepTUI("Getting MongoDB password"):
        try:
            return subprocess.check_output(
                'kubectl get secret --namespace default mongodb -o jsonpath="{.data.mongodb-password}" | '
                'base64 --decode',
                shell=True,
            ).decode("utf-8")
        except subprocess.CalledProcessError as e:
            raise EdgeException(f"Error occurred while getting MongoDB password\n{e.output}")


def get_lb_ip(name) -> str:
    try:
        return subprocess.check_output(
            f'kubectl get service --namespace default {name} -o jsonpath="{{.status.loadBalancer.ingress[0].ip}}"',
            shell=True,
        ).decode("utf-8")
    except subprocess.CalledProcessError as e:
        raise EdgeException(f"Error occurred while getting IP for {name}\n{e.output}")


def check_mongodb_installed() -> bool:
    helm_charts = json.loads(subprocess.check_output("helm list -o json", shell=True).decode("utf-8"))
    for chart in helm_charts:
        if chart["name"] == "mongodb":
            return True
    return False


def check_mongodb_lb_installed() -> bool:
    try:
        subprocess.check_output("kubectl get service mongodb-lb -o json", stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        if e.output.decode("utf-8") == 'Error from server (NotFound): services "mongodb-lb" not found\n':
            return False
        else:
            raise e
    return True


def install_mongodb() -> (str, str):
    with SubStepTUI("Checking if MongoDB is installed on the cluster") as sub_step:
        try:
            if not check_mongodb_installed():
                sub_step.update("Installing MongoDB on the cluster")
                subprocess.check_output(
                    """
                    helm repo add bitnami https://charts.bitnami.com/bitnami
                    helm upgrade -i --wait mongodb bitnami/mongodb --set auth.username=sacred,auth.database=sacred
                """,
                    shell=True,
                )
                sub_step.update("MongoDB is installed on the cluster", status=TUIStatus.SUCCESSFUL)
        except subprocess.CalledProcessError as e:
            raise EdgeException(f"Error occurred while installing MongoDB with helm chart\n{e.output}")

    with SubStepTUI("Making MongoDB externally available"):
        try:
            if not check_mongodb_lb_installed():
                subprocess.check_output(
                    "kubectl expose deployment mongodb --name mongodb-lb --type LoadBalancer --port 60000 "
                    "--target-port 27017",
                    shell=True,
                )
        except subprocess.CalledProcessError as e:
            raise EdgeException(f"Error occurred while exposing MongoDB\n{e.output}")

    password = get_mongodb_password()

    with SubStepTUI("Getting MongoDB IP address (may take a few minutes)"):
        external_ip = get_lb_ip("mongodb-lb")
        while external_ip == "":
            time.sleep(5)
            external_ip = get_lb_ip("mongodb-lb")

    internal_connection_string = f"mongodb://sacred:{password}@mongodb/sacred"
    external_connection_string = f"mongodb://sacred:{password}@{external_ip}:60000/sacred"

    with SubStepTUI("Saving MongoDB credentials into kubernetes secrets") as sub_step:
        try:
            subprocess.check_output(
                "kubectl delete secret mongodb-connection", shell=True, stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as exc:
            if "NotFound" in exc.output.decode("utf-8"):
                pass  # error expected if the secret was not previously created
            else:
                raise EdgeException(
                    f"Error while trying to delete mongodb-connection secret\n{exc.output.decode('utf-8')}"
                )
        try:
            subprocess.check_output(
                f"kubectl create secret generic mongodb-connection "
                f"--from-literal=internal={internal_connection_string}",
                shell=True,
            )
        except subprocess.CalledProcessError as exc:
            raise EdgeException(
                f"Error while trying to create mongodb-connection secret\n{exc.output.decode('utf-8')}"
            )

        sub_step.update(status=TUIStatus.SUCCESSFUL)
        sub_step.add_explanation(f"Internal connection string: mongodb://sacred:*****@mongodb/sacred")
        sub_step.add_explanation(f"External connection string: mongodb://sacred:*****@{external_ip}:60000/sacred")
        sub_step.add_explanation(f"You can get full connection strings by running `./edge.sh experiments get-mongodb`")

    return internal_connection_string, external_connection_string


def install_omniboard() -> str:
    with SubStepTUI("Installing experiment tracker dashboard (Omniboard)"):
        try:
            subprocess.check_output("kubectl apply -f /src/edge/k8s/omniboard.yaml", shell=True)
        except subprocess.CalledProcessError as e:
            raise EdgeException(f"Error occurred while applying Omniboard's configuration\n {e}")

    with SubStepTUI("Getting Omniboard IP address (may take a few minutes)") as sub_step:
        external_ip = get_lb_ip("omniboard-lb")
        while external_ip == "":
            time.sleep(5)
            external_ip = get_lb_ip("omniboard-lb")

        sub_step.update(status=TUIStatus.SUCCESSFUL)
        sub_step.add_explanation(
            f"Omniboard is installed and available at http://{external_ip}:9000",
        )
    return f"http://{external_ip}:9000"


def save_mongo_to_secretmanager(project_id: str, secret_id: str, connection_string: str):
    with SubStepTUI("Saving MongoDB credentials to Google Cloud Secret Manager") as sub_step:
        try:
            client = secretmanager_v1.SecretManagerServiceClient()
            try:
                client.access_secret_version(name=f"projects/{project_id}/secrets/{secret_id}/versions/latest")
            except NotFound:
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
                    "payload": {"data": connection_string.encode()},
                }
            )
        except PermissionDenied as exc:
            sub_step.update(status=TUIStatus.FAILED)
            sub_step.add_explanation(exc.message)


def delete_mongo_to_secretmanager(_config: EdgeConfig):
    project_id = _config.google_cloud_project.project_id
    secret_id = _config.experiments.mongodb_connection_string_secret
    print("## Removing MongoDB connection string from Google Cloud Secret Manager")
    client = secretmanager_v1.SecretManagerServiceClient()

    try:
        client.access_secret_version(name=f"projects/{project_id}/secrets/{secret_id}/versions/latest")
        client.delete_secret(name=f"projects/{project_id}/secrets/{secret_id}")
    except NotFound:
        print("Secret does not exist")
        return


def delete_cluster(_config: EdgeConfig):
    project_id = _config.google_cloud_project.project_id
    region = _config.google_cloud_project.region
    cluster_name = _config.experiments.gke_cluster_name
    print(f"## Deleting cluster '{cluster_name}'")
    client = container_v1.ClusterManagerClient()
    try:
        client.get_cluster(
            project_id=project_id, name=f"projects/{project_id}/locations/{region}/clusters/{cluster_name}"
        )
        os.system(f"gcloud container clusters delete {cluster_name} --project {project_id} --region {region}")
    except NotFound:
        print("Cluster does not exist")


def setup_sacred(project_id: str, region: str, gke_cluster_name: str, secret_id: str) -> SacredState:
    with StepTUI("Installing experiment tracker", emoji="📔"):
        create_cluster(
            project_id, region, gke_cluster_name
        )

        get_credentials(
            project_id, region, gke_cluster_name
        )

        internal_mongo_string, external_mongo_string = install_mongodb()

        save_mongo_to_secretmanager(project_id, secret_id, external_mongo_string)

        external_omniboard_string = install_omniboard()

    return SacredState(external_omniboard_string=external_omniboard_string)


def tear_down_sacred(_config: EdgeConfig, _state: EdgeState):
    print("# Tearing down Sacred+Omniboard")

    delete_mongo_to_secretmanager(_config)
    delete_cluster(_config)


def get_connection_string(project_id: str, secret_id: str) -> str:
    client = secretmanager_v1.SecretManagerServiceClient()

    secret_name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(name=secret_name)

    return response.payload.data.decode("UTF-8")


def track_experiment(config: EdgeConfig, state: EdgeState, experiment: Experiment):
    if config is None or state is None:
        print("Vertex:edge configuration is not provided, the experiment will not be tracked")
        return

    if state.sacred is None:
        print("Experiment tracker is not initialised in vertex:edge, the experiment will not be tracked")
        return

    project_id = config.google_cloud_project.project_id
    secret_id = config.experiments.mongodb_connection_string_secret
    mongo_connection_string = get_connection_string(project_id, secret_id)
    experiment.observers.append(MongoObserver(mongo_connection_string))
