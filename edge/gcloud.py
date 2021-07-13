import subprocess
from typing import List


def get_gcp_regions(project: str) -> List[str]:
    result = subprocess.check_output(f"gcloud compute regions list --project {project}", shell=True).decode("utf-8")
    rows = result.split("\n")[1:-1]
    regions = [row.split(" ")[0] for row in rows]
    return regions
