import sys
from dataclasses import dataclass
from serde import serialize
from serde.yaml import to_yaml
from edge.config import EdgeConfig, ModelConfig
from edge.state import ModelState, EdgeState


@serialize
@dataclass
class Description:
    config: ModelConfig
    state: ModelState


def describe_model(model_name):
    with EdgeConfig.context(silent=True) as config:
        if model_name not in config.models:
            print(f"'{model_name}' model is not initialised. "
                  f"Initialise it by running `./edge.sh model init {model_name}`")
            sys.exit(1)
        else:
            with EdgeState.context(config, silent=True) as state:
                description = Description(
                    config.models[model_name],
                    state.models[model_name]
                )
                print(to_yaml(description))
                sys.exit(0)
