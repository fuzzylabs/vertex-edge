import sys

from edge.config import EdgeConfig
from edge.sacred import get_connection_string
from edge.state import EdgeState


def get_mongodb():
    with EdgeConfig.context(silent=True) as config:
        with EdgeState.context(config, silent=True) as state:
            project_id = config.google_cloud_project.project_id
            secret_id = config.experiments.mongodb_connection_string_secret
            print(get_connection_string(project_id, secret_id))
            sys.exit(0)
