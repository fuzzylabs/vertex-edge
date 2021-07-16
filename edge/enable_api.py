import os
from .config import EdgeConfig


def enable_api(_config: EdgeConfig):
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
