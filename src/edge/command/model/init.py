import os
import time
from edge.command.common.precommand_check import precommand_checks
from edge.config import EdgeConfig, ModelConfig
from edge.enable_api import enable_service_api
from edge.endpoint import setup_endpoint
from edge.exception import EdgeException
from edge.state import EdgeState
from edge.tui import TUI, StepTUI, SubStepTUI, TUIStatus, qmark
from edge.path import get_model_dvc_pipeline
import questionary


def model_init(model_name: str):
    intro = f"Initialising model '{model_name}' on Vertex AI"
    success_title = "Model initialised successfully"
    success_message = f"""
What's next? We suggest you proceed with:

  Train and deploy a model (see 'Training a model' section of the README for more details):
    dvc repro {get_model_dvc_pipeline(model_name)}
    ./edge.sh model deploy

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

                with StepTUI(f"Configuring model '{model_name}'", emoji="⚙️"):
                    with SubStepTUI(f"Checking if model '{model_name}' is configured") as sub_step:
                        if model_name in config.models:
                            sub_step.update(f"Model '{model_name}' is already configured", status=TUIStatus.WARNING)
                            sub_step.set_dirty()
                            if not questionary.confirm(
                                f"Do you want to configure model '{model_name}' again?",
                                qmark=qmark
                            ).ask():
                                raise EdgeException(f"Configuration for model '{model_name}' already exists")
                        else:
                            sub_step.update(
                                message=f"Model '{model_name}' is not configured",
                                status=TUIStatus.NEUTRAL
                            )
                    with SubStepTUI(f"Creating model '{model_name}' configuration"):
                        model_config = ModelConfig(
                            name=model_name,
                            endpoint_name=f"{model_name}-endpoint"
                        )
                        config.models[model_name] = model_config

                endpoint_name = config.models[model_name].endpoint_name

                model_state = setup_endpoint(
                    config.google_cloud_project.project_id,
                    config.google_cloud_project.region,
                    endpoint_name
                )

                directory_exists = False
                pipeline_exists = False
                with StepTUI("Checking project directory structure", emoji="📁"):
                    with SubStepTUI(f"Checking that 'models/{model_name}' directory exists") as sub_step:
                        if not (os.path.exists(f"models/{model_name}") and os.path.isdir(f"models/{model_name}")):
                            sub_step.update(
                                message="'models/{model_name}' directory does not exist",
                                status=TUIStatus.NEUTRAL
                            )
                        else:
                            directory_exists = True
                    if directory_exists:
                        with SubStepTUI(f"Checking that 'models/{model_name}/dvc.yaml' pipeline exists") as sub_step:
                            if not os.path.exists(f"models/{model_name}/dvc.yaml"):
                                sub_step.update(
                                    message=f"'models/{model_name}/dvc.yaml' pipeline does not exist",
                                    status=TUIStatus.NEUTRAL
                                )
                            else:
                                pipeline_exists = True

                state.models = {
                    model_name: model_state
                }

                if not directory_exists or not pipeline_exists:
                    tui.success_message = f"Note that the 'models/{model_name}" + tui.success_message
