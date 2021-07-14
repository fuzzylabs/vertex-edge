import os
from .config import EdgeConfig


def enable_api(_config: EdgeConfig):
    print("# Enabling necessary Google Cloud APIs")
    project_id = _config.google_cloud_project.project_id

    print("## Kubernetes Engine")
    os.system(f"gcloud services enable container.googleapis.com --project {project_id}")

    print("## Storage")
    os.system(f"gcloud services enable storage-component.googleapis.com --project {project_id}")

    print("## Container Registry")
    os.system(f"gcloud services enable containerregistry.googleapis.com --project {project_id}")

    print("## Vertex AI")
    os.system(f"gcloud services enable aiplatform.googleapis.com --project {project_id}")

    print("## Secret Manager")
    os.system(f"gcloud services enable secretmanager.googleapis.com --project {project_id}")

    print("## Cloud Run")
    os.system(f"gcloud services enable run.googleapis.com --project {project_id}")
