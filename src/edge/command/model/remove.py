import questionary

from edge.command.common.precommand_check import precommand_checks
from edge.config import EdgeConfig
from edge.endpoint import tear_down_endpoint
from edge.exception import EdgeException
from edge.state import EdgeState
from edge.tui import TUI, StepTUI, SubStepTUI, TUIStatus, qmark


def remove_model(model_name):
    intro = f"Removing model '{model_name}' from vertex:edge"
    success_title = "Model removed successfully"
    success_message = "Success"
    failure_title = "Model removal failed"
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
            with EdgeState.context(config, to_save=True, to_lock=True) as state:
                with StepTUI(f"Checking model '{model_name}' configuration and state", emoji="🐏"):
                    with SubStepTUI(f"Checking model '{model_name}' configuration"):
                        if model_name not in config.models:
                            raise EdgeException(f"'{model_name}' model is not in `edge.yaml` configuration, so it "
                                                f"cannot be removed.")
                    with SubStepTUI(f"Checking model '{model_name}' state"):
                        if model_name not in state.models:
                            raise EdgeException(f"'{model_name}' is not in vertex:edge state, which suggests that "
                                                f"it has not been initialised. Cannot be removed")
                    with SubStepTUI("Confirming action", status=TUIStatus.WARNING) as sub_step:
                        sub_step.add_explanation(f"This action will undeploy '{model_name}' model from Vertex AI, "
                                                 f"delete the Vertex AI endpoint associated with '{model_name}' model, "
                                                 f"and remove '{model_name}' model from vertex:edge config and "
                                                 f"state.")
                        if not questionary.confirm("Do you want to continue?", qmark=qmark, default=False).ask():
                            raise EdgeException("Canceled by user")

                with StepTUI(f"Removing '{model_name}' model"):
                    with SubStepTUI(f"Deleting '{state.models[model_name].endpoint_resource_name}' endpoint"):
                        tear_down_endpoint(state.models[model_name].endpoint_resource_name)
                    with SubStepTUI(f"Removing '{model_name}' model from config and state"):
                        del config.models[model_name]
                        del state.models[model_name]

