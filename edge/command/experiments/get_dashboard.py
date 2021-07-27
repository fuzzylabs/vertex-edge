import sys

from edge.config import EdgeConfig
from edge.state import EdgeState


def get_dashboard():
    with EdgeConfig.context(silent=True) as config:
        with EdgeState.context(config, silent=True) as state:
            print(state.sacred.external_omniboard_string)
            sys.exit(0)
