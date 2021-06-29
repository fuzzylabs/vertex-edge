import os
from .config import EdgeConfig


def enable_api(_config: EdgeConfig):
    print("# Enabling necessary Google Cloud APIs")

    print("## Kubernetes Engine")
    os.system("gcloud services enable container.googleapis.com")

    print("## Storage")
    os.system("gcloud services enable storage-component.googleapis.com")

    print("## Container Registry")
    os.system("gcloud services enable containerregistry.googleapis.com")

    print("## Vertex AI")
    os.system("gcloud services enable aiplatform.googleapis.com")

    print("## Secret Manager")
    os.system("gcloud services enable secretmanager.googleapis.com")
