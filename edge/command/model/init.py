import time
from edge.command.common.precommand_check import precommand_checks
from edge.config import EdgeConfig, ModelConfig
from edge.docker import build_docker, push_docker
from edge.enable_api import enable_service_api
from edge.endpoint import setup_endpoint
from edge.exception import EdgeException
from edge.state import EdgeState
from edge.tui import TUI, StepTUI, SubStepTUI, TUIStatus, qmark
from edge.path import get_model_dvc_pipeline
import questionary


def model_init():
    intro = "Initialising model on Vertex AI"
    success_title = "Model initialised successfully"
    success_message = f"""
What's next? We suggest you proceed with:

  Train and deploy a model (see X section of the README for more details):
    dvc repro {get_model_dvc_pipeline()}
    ./edge.py model deploy

Happy herding! 🐏
        """.strip()
    failure_title = "Model initialisation failed"
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
                    with SubStepTUI("Enabling Vertex AI API for model training and deployment"):
                        enable_service_api("aiplatform.googleapis.com", config.google_cloud_project.project_id)
                    with SubStepTUI("Enabling Container Registry API for Docker images"):
                        enable_service_api(
                            "containerregistry.googleapis.com",
                            config.google_cloud_project.project_id
                        )

                with StepTUI("Configuring model", emoji="⚙️"):
                    with SubStepTUI("Configuring model name", status=TUIStatus.NEUTRAL):
                        previous_model_name = config.models[0].name if len(config.models) > 0 else ""
                        model_name = questionary.text(
                            "Choose a name for your model:",
                            default=previous_model_name,
                            qmark=qmark,
                            validate=(lambda x: x.strip() != "")
                        ).ask()
                        if model_name is None:
                            raise EdgeException("Model name is required")
                        model_name = model_name.strip()
                        model_config = ModelConfig(
                            name=model_name,
                            prediction_server_image=f"gcr.io/{config.google_cloud_project.project_id}/"
                                                    f"{model_name}-prediction",
                            endpoint_name=f"{model_name}-endpoint"
                        )
                        config.models = [model_config]

                image_name = config.models[0].prediction_server_image

                endpoint_name = config.models[0].endpoint_name

                model_state = setup_endpoint(
                    config.google_cloud_project.project_id,
                    config.google_cloud_project.region,
                    endpoint_name
                )

                state.models = {
                    model_name: model_state
                }
