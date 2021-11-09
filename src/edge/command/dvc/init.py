import os

from edge.command.common.precommand_check import precommand_checks
from edge.config import EdgeConfig
from edge.state import EdgeState
from edge.tui import TUI
from edge.dvc import setup_dvc
from edge.path import get_model_dvc_pipeline


def dvc_init():
    intro = "Initialising data version control (DVC)"
    success_title = "DVC initialised successfully"
    success_message = f"""
Now you can version your data using DVC. See https://dvc.org/doc for more details about how it can be used. 

What's next? We suggest you proceed with:

  Train and deploy a model (see 'Training a model' section of the README for more details):
    ./edge.sh model init fashion
    dvc repro {get_model_dvc_pipeline("fashion")}
    ./edge.sh model deploy fashion

Happy herding! 🐏
    """.strip()
    failure_title = "DVC initialisation failed"
    failure_message = "See the errors above. See README for more details."
    with TUI(
        intro,
        success_title,
        success_message,
        failure_title,
        failure_message
    ) as tui:
        with EdgeConfig.context() as config:
            precommand_checks(config)
            with EdgeState.context(config) as state:
                setup_dvc(
                    state.storage.bucket_path,
                    config.storage_bucket.dvc_store_directory
                )

