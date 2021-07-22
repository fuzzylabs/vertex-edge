from edge.config import EdgeConfig
from edge.state import EdgeState
from edge.tui import TUI
from edge.dvc import setup_dvc


def dvc_init(config: EdgeConfig):
    intro = "Initialising data version control (DVC)"
    success_title = "DVC is initialised"
    success_message = "success"
    failure_title = "DVC failed to initialise"
    failure_message = "failure"
    with TUI(
        intro,
        success_title,
        success_message,
        failure_title,
        failure_message
    ) as tui:
        with EdgeState.load(config) as state:
            setup_dvc(
                state.storage_bucket_state.bucket_path,
                config.storage_bucket.dvc_store_directory
            )

