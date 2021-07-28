import json
import os

from edge.command.common.precommand_check import precommand_checks
from edge.config import EdgeConfig
from edge.exception import EdgeException
from edge.state import EdgeState
from edge.tui import TUI, StepTUI, SubStepTUI
from edge.vertex_deploy import vertex_deploy
from edge.path import get_model_dvc_pipeline


def model_deploy():
    intro = "Deploying model on Vertex AI"
    success_title = "Model deployed successfully"
    success_message = "Success"
    failure_title = "Model deployment failed"
    failure_message = "See the errors above. See README for more details."
    with EdgeConfig.context() as config:
        with TUI(
                intro,
                success_title,
                success_message,
                failure_title,
                failure_message
        ) as tui:
            precommand_checks(config)
            with EdgeState.context(config, to_lock=True) as state:
                with StepTUI("Checking model configuration", emoji="🐏"):
                    with SubStepTUI("Checking that the model is initialised"):
                        if len(config.models) == 0:
                            raise EdgeException("Model has not been initialised. "
                                                "Run `./edge.sh model init` to initialise.")
                        model_name = config.models[0].name
                        if state.models is None or state.models[model_name] is None:
                            raise EdgeException("Model is missing from vertex:edge state. "
                                                "This might mean that the model has not been initialised. "
                                                "Run `./edge.sh model init` to initialise.")
                        endpoint_resource_name = state.models[model_name].endpoint_resource_name
                    with SubStepTUI("Checking that the model has been trained"):
                        if not os.path.exists("models/fashion/vertex_model.json"):
                            raise EdgeException("models/fashion/vertex_model.json does not exist. "
                                                "This means that the model has not been"
                                                " trained. To train the model, "
                                                f"run `dvc repro {get_model_dvc_pipeline()}`")
                        with open("models/fashion/vertex_model.json") as file:
                            model_dict = json.load(file)
                        model_resource_name = model_dict["model_name"]
                vertex_deploy(endpoint_resource_name, model_resource_name, model_name)

                short_endpoint_resource_name = "/".join(endpoint_resource_name.split("/")[2:])
                tui.success_message = (
                    "You can see the deployed model at "
                    f"https://console.cloud.google.com/vertex-ai/"
                    f"{short_endpoint_resource_name}?project={config.google_cloud_project.project_id}\n\n"
                    "Happy herding! 🐏"
                )

