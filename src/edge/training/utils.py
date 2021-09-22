import os
import uuid

from edge.config import EdgeConfig
from edge.state import EdgeState
from google.cloud import storage
from google.cloud.storage.blob import Blob


def wrap_open(path: str, mode: str = "r"):
    if path.startswith("gs://"):

        client = storage.Client()

        return Blob.from_string(path, client).open(mode=mode)
    else:
        return open(path, mode=mode)


# TODO: remove
def get_vertex_paths(_config: EdgeConfig, state: EdgeState):
    staging_path = os.path.join(state.storage.bucket_path, _config.storage_bucket.vertex_jobs_directory)
    output_path = os.path.join(staging_path, str(uuid.uuid4()))

    return staging_path, output_path
