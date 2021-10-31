import os

from edge.command.common.precommand_check import precommand_checks
from edge.config import EdgeConfig
from edge.exception import EdgeException
from edge.state import EdgeState
from edge.tui import TUI, StepTUI, SubStepTUI, TUIStatus, qmark
from cookiecutter.main import cookiecutter
from cookiecutter.exceptions import OutputDirExistsException
import questionary


def create_model_from_template(model_name: str, force: bool = False):
    intro = f"Creating model pipeline '{model_name}' from a template"
    success_title = "Pipeline is created from a template"
    success_message = "Success"
    failure_title = "Pipeline creation failed"
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
            with EdgeState.context(config) as state:
                with StepTUI("Checking model configuration", emoji="🐏"):
                    with SubStepTUI("Checking that the model is initialised"):
                        if model_name not in config.models:
                            raise EdgeException("Model has not been initialised. "
                                                f"Run `./edge.sh model init {model_name}` to initialise.")
                        if state.models is None or state.models[model_name] is None:
                            raise EdgeException("Model is missing from vertex:edge state. "
                                                "This might mean that the model has not been initialised. "
                                                f"Run `./edge.sh model init {model_name}` to initialise.")
                with StepTUI("Creating pipeline from a template", emoji="🐏"):
                    with SubStepTUI("Choosing model pipeline template", status=TUIStatus.NEUTRAL) as substep:
                        substep.set_dirty()
                        templates = {
                            "tensorflow": "tensorflow_model",
                        }
                        pipeline_template = questionary.select(
                            "Choose model template",
                            templates.keys(),
                            qmark=qmark
                        ).ask()
                        if pipeline_template is None:
                            raise EdgeException("Pipeline template must be selected")
                        pipeline_template = templates[pipeline_template]
                    with SubStepTUI(f"Applying template '{pipeline_template}'"):
                        try:
                            cookiecutter(
                                os.path.join(
                                    os.path.dirname(os.path.abspath(__file__)),
                                    f"../../templates/{pipeline_template}/"
                                ),
                                output_dir="models/",
                                extra_context={
                                    "model_name": model_name
                                },
                                no_input=True,
                                overwrite_if_exists=force,
                            )
                        except OutputDirExistsException as exc:
                            raise EdgeException(
                                f"Pipeline directory 'models/{model_name}' already exists, so the template cannot be "
                                f"applied. If you want to override the existing pipeline, run `edge model template "
                                f"{model_name} -f`."
                            )
