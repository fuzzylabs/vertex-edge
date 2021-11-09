import sys

from edge.config import EdgeConfig
from edge.state import EdgeState
import questionary


def get_model_endpoint(model_name: str):
    with EdgeConfig.context(silent=True) as config:
        if config.models is None or model_name not in config.models:
            questionary.print("Model is not initialised. Initialise it by running `./edge.sh model init`.",
                              style="fg:ansired")
            sys.exit(1)
        with EdgeState.context(config, silent=True) as state:
            print(state.models[model_name].endpoint_resource_name)
            sys.exit(0)
