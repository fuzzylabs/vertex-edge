import json
import os
import subprocess
from typing import List
from .exception import EdgeException

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
    return (
        subprocess.check_output("gcloud config get-value account", shell=True, stderr=subprocess.DEVNULL)
        .decode("utf-8")
        .strip()
    )


def get_gcloud_project() -> str:
    return (
        subprocess.check_output("gcloud config get-value project", shell=True, stderr=subprocess.DEVNULL)
        .decode("utf-8")
        .strip()
    )


def get_gcloud_region() -> str:
    return (
        subprocess.check_output("gcloud config get-value compute/region", shell=True, stderr=subprocess.DEVNULL)
        .decode("utf-8")
        .strip()
    )


def is_billing_enabled(project: str) -> bool:
    try:
        response = json.loads(
            subprocess.check_output(
                f"gcloud alpha billing projects describe {project} --format json", shell=True, stderr=subprocess.DEVNULL
            )
        )
        return response["billingEnabled"]
    except subprocess.CalledProcessError:
        raise EdgeException(
            f"Unable to access billing for project {project}. Check project id and your permissions in "
            f"Google Cloud."
        )


def is_authenticated() -> (bool, str):
    """
    Check if gcloud is authenticated
    :return: is authenticated, and the reason if not
    """
    try:
        subprocess.check_output(f"gcloud auth print-access-token", shell=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return False, "gcloud is not authenticated. Run `gcloud auth login`."

    try:
        subprocess.check_output(
            f"gcloud auth application-default print-access-token", shell=True, stderr=subprocess.DEVNULL
        )
        return True, ""
    except subprocess.CalledProcessError:
        return (
            False,
            "gcloud does not have application default credentials configured. "
            "Run `gcloud auth application-default login`.",
        )
