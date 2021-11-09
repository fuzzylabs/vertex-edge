import sys

from edge.config import EdgeConfig


def list_models():
    with EdgeConfig.context(silent=True) as config:
        print("Configured models:")
        print("\n".join([f" - {x}" for x in config.models.keys()]))
        sys.exit(0)
