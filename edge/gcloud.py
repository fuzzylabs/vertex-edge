import subprocess
from typing import List


def get_gcp_regions() -> List[str]:
    result = subprocess.check_output("gcloud compute regions list", shell=True).decode("utf-8")
    rows = result.split("\n")[1:-1]
    regions = [row.split(" ")[0] for row in rows]
    return regions
