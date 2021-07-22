from edge.command.common.precommand_check import precommand_checks
from edge.config import EdgeConfig
from edge.state import EdgeState
from edge.tui import TUI
from edge.dvc import setup_dvc


def dvc_init(config: EdgeConfig):
    intro = "Initialising data version control (DVC)"
    success_title = "DVC initialised successfully"
    success_message = """
What's next? We suggest you proceed with:

  Train and deploy a model (see X section of the README for more details):
    ./edge.py vertex init
    dvc repro ...
    ./edge.py vertex deploy

Happy herding! 🐏
    """.strip()
    failure_title = "DVC initialisation failed"
    failure_message = "See the errors above. For technical details see error log. See README for more details."
    with TUI(
        intro,
        success_title,
        success_message,
        failure_title,
        failure_message
    ) as tui:
        precommand_checks(config)
        with EdgeState.load(config) as state:
            setup_dvc(
                state.storage_bucket_state.bucket_path,
                config.storage_bucket.dvc_store_directory
            )

