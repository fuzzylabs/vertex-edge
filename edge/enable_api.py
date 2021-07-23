"""
Enabling Google Cloud APIs
"""
import json
import os
import subprocess
from .exception import EdgeException
from .config import EdgeConfig


def enable_api(_config: EdgeConfig):
    """
    Enable all necessary APIs (deprecated)

    :param _config:
    :return:
    """
    print("# Enabling necessary Google Cloud APIs")
    project_id = _config.google_cloud_project.project_id

    print("## Kubernetes Engine")
    print("Required for installing the experiment tracker")
    os.system(f"gcloud services enable container.googleapis.com --project {project_id}")

    print("## Storage")
    print("Required for DVC remote storage, Vertex AI artifact storage, and Vertex:Edge state")
    os.system(f"gcloud services enable storage-component.googleapis.com --project {project_id}")

    print("## Container Registry")
    print("Required for hosting of the webapp and prediction server Docker images hosting.")
    os.system(f"gcloud services enable containerregistry.googleapis.com --project {project_id}")

    print("## Vertex AI")
    print("Required for training and deploying on Vertex AI")
    os.system(f"gcloud services enable aiplatform.googleapis.com --project {project_id}")

    print("## Secret Manager")
    print("Required for secret sharing, including connection strings for the experiment tracker")
    os.system(f"gcloud services enable secretmanager.googleapis.com --project {project_id}")

    print("## Cloud Run")
    print("Required for deploying the webapp")
    os.system(f"gcloud services enable run.googleapis.com --project {project_id}")


def is_service_api_enabled(service_name: str, project_id: str) -> bool:
    """
    Check if a [service_name] API is enabled

    :param service_name:
    :param project_id:
    :return:
    """
    try:
        enabled_services = json.loads(subprocess.check_output(
            f"gcloud services list --enabled --project {project_id} --format json",
            shell=True,
            stderr=subprocess.STDOUT
        ).decode("utf-8"))
        for service in enabled_services:
            if service_name in service["name"]:
                return True
        return False
    except subprocess.CalledProcessError as error:
        parse_enable_service_api_error(service_name, error)
        return False


def enable_service_api(service: str, project_id: str):
    """
    Enable [service] API

    :param service:
    :param project_id:
    :return:
    """
    if not is_service_api_enabled(service, project_id):
        try:
            subprocess.check_output(
                f"gcloud services enable {service} --project {project_id}",
                shell=True,
                stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as error:
            parse_enable_service_api_error(service, error)


def parse_enable_service_api_error(service: str, error: subprocess.CalledProcessError):
    """
    Parse errors coming from `gcloud services` commands

    :param service:
    :param error:
    :return:
    """
    output = error.output.decode("utf-8")
    if output.startswith("ERROR: (gcloud.services.enable) PERMISSION_DENIED"):
        raise EdgeException(f"Service '{service}' cannot be enabled because you have insufficient permissions "
                            f"on Google Cloud")

    raise error
