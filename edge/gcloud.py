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
