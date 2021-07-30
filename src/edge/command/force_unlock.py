import sys

from edge.config import EdgeConfig
from edge.state import EdgeState


def force_unlock():
    with EdgeConfig.context() as config:
        EdgeState.unlock(
            config.google_cloud_project.project_id,
            config.storage_bucket.bucket_name,
        )
        sys.exit(0)
