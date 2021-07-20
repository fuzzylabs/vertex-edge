import os
import subprocess
from typing import List

# Regions that are supported for Vertex AI training and deployment
regions = [
    "us-central1",
    "europe-west4",
    "asia-east1",
    "asia-northeast1",
    "asia-northeast3",
    "asia-southeast1",
    "australia-southeast1",
    "europe-west1",
    "europe-west2",
    "northamerica-northeast1",
    "us-west1",
    "us-east1",
    "us-east4",
]


def get_gcp_regions(project: str) -> List[str]:
    return regions


def get_gcloud_account() -> str:
    return subprocess.check_output("gcloud config get-value account", shell=True, stderr=subprocess.DEVNULL).decode("utf-8").strip()


def get_gcloud_project() -> str:
    return subprocess.check_output("gcloud config get-value project", shell=True, stderr=subprocess.DEVNULL).decode("utf-8").strip()


def get_gcloud_region() -> str:
    return subprocess.check_output("gcloud config get-value compute/region", shell=True, stderr=subprocess.DEVNULL).decode("utf-8").strip()
