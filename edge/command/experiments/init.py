from edge.command.common.precommand_check import precommand_checks
from edge.config import EdgeConfig, SacredConfig
from edge.enable_api import enable_service_api
from edge.exception import EdgeException
from edge.path import get_model_dvc_pipeline
from edge.state import EdgeState
from edge.tui import TUI, StepTUI, SubStepTUI, TUIStatus, qmark
from edge.sacred import setup_sacred
import questionary


def experiments_init():
    intro = "Initialising experiment tracking"
    success_title = "Experiment tracking initialised successfully"
    success_message = ""
    failure_title = "Experiment tracking initialisation failed"
    failure_message = "See the errors above. See README for more details."
    with TUI(
        intro,
        success_title,
        success_message,
        failure_title,
        failure_message
    ) as tui:
        with EdgeConfig.context(to_save=True) as config:
            precommand_checks(config)
            with EdgeState.context(config, to_lock=True, to_save=True) as state:
                with StepTUI("Enabling required Google Cloud APIs", emoji="☁️"):
                    with SubStepTUI("Enabling Kubernetes Engine API for experiment tracking"):
                        enable_service_api("container.googleapis.com", config.google_cloud_project.project_id)
                with StepTUI("Configuring experiment tracking", emoji="⚙️"):
                    with SubStepTUI("Configuring Kubernetes cluster name on GCP", status=TUIStatus.NEUTRAL) as sub_step:
                        sub_step.add_explanation("If a name for an existing cluster is provided, this cluster "
                                                 "will be used. Otherwise, vertex:edge will create a cluster with GKE "
                                                 "auto-pilot.")
                        previous_cluster_name = (
                            config.experiments.gke_cluster_name if config.experiments is not None else "sacred"
                        )
                        cluster_name = questionary.text(
                            "Choose a name for a kubernetes cluster to use:",
                            default=previous_cluster_name,
                            qmark=qmark,
                            validate=(lambda x: x.strip() != "")
                        ).ask()
                        if cluster_name is None:
                            raise EdgeException("Cluster name is required")
                        sacred_config = SacredConfig(
                            gke_cluster_name=cluster_name,
                            mongodb_connection_string_secret="sacred-mongodb-connection-string"
                        )
                        config.experiments = sacred_config
                sacred_state = setup_sacred(
                    config.google_cloud_project.project_id,
                    config.google_cloud_project.region,
                    config.experiments.gke_cluster_name,
                    config.experiments.mongodb_connection_string_secret,
                )
                state.sacred = sacred_state
                tui.success_title = (
                    f"Now you can track experiments, and view them in Omniboard dashboard "
                    f"at {sacred_state.external_omniboard_string}\n\n"
                    "What's next? We suggest you proceed with:\n\n"
                    "  Train and deploy a model (see X section of the README for more details):\n"
                    "    ./edge.sh model init\n"
                    f"    dvc repro {get_model_dvc_pipeline()}\n"
                    "    ./edge.sh model deploy\n\n"
                    "Happy herding! 🐏"
                )



