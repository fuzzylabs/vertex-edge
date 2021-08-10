import inspect
import json
import os
import subprocess
import sys
from collections import OrderedDict
from typing import List, Optional

from edge.state import EdgeState
from edge.training.sacred import to_sacred_params_for_vertex
from edge.training.utils import get_vertex_paths
from serde import serialize, deserialize
from serde.json import to_json
from dataclasses import dataclass
from google.cloud import storage
from google.cloud.aiplatform import Model, CustomJob
from sacred.experiment import Experiment
from edge.config import ModelConfig, GCProjectConfig, EdgeConfig
from edge.exception import EdgeException
from edge.tui import TUI, StepTUI, SubStepTUI
from edge.path import get_default_config_path_from_model


@dataclass
class TrainedModel:
    model_name: Optional[str]
    is_local: bool = False

    @classmethod
    def from_vertex_model(cls, model: Model):
        return TrainedModel(
            model_name=model.resource_name,
        )

    @classmethod
    def from_local_model(cls):
        return TrainedModel(
            model_name=None,
            is_local=True,
        )


def run_job_locally(
        _run: Experiment,
        model_config: ModelConfig,
        training_script_args: List[str],
        training_script_path: str = "train.py",
):
    """
    A wrapper to run a training job locally

    :param _run: Sacred experiment instance, to record progress to
    :param model_config: Vertex:edge model configuration
    :param training_script_args: Arguments to pass to the training script
    :param training_script_path: Training script path, default: train.py
    :return:
    """
    with TUI(
            f"Running a custom training job locally for '{model_config.name}'",
            "Custom job finished successfully",
            "",
            "Custom training job failed",
            "",
    ) as tui:
        with StepTUI("Training locally"):
            with SubStepTUI("Running a training job locally") as sub_step:
                try:
                    subprocess.check_output(
                        f"python {training_script_path} {' '.join(training_script_args)}",
                        shell=True,
                        stderr=subprocess.STDOUT,
                    )
                except subprocess.CalledProcessError as exc:
                    raise EdgeException(
                        "Error while runnning the training script:\n"
                        f"{exc.output.decode('utf-8')}"
                    )
                pass
            with SubStepTUI("Recording results to experiment tracker"):
                with open("metrics.json") as f:
                    metrics = json.load(f)
                for metric in metrics:
                    _run.log_scalar(metric, metrics[metric])
        with StepTUI("Creating trained model"):
            with SubStepTUI("Saving results locally"):
                with open("trained_model.json", "w") as f:
                    f.write(to_json(TrainedModel.from_local_model()))


def run_job_on_vertex(
        _run: Experiment,
        model_config: ModelConfig,
        gcp_config: GCProjectConfig,
        requirements: List[str],
        training_script_args: List[str],
        staging_bucket: str,
        output_dir: str,
        training_script_path: str = "train.py"
):
    """
    A wrapper for a training procedure on Vertex AI

    :param _run: Sacred experiment instance, to record progress to
    :param model_config: Vertex:edge model configuration
    :param gcp_config: Vertex:edge GCP configuration
    :param requirements: Additional pip requirements for a training container
    :param training_script_args: Arguments to pass to the training script
    :param staging_bucket: Vertex AI staging bucket
    :param output_dir: Google Storage URI for output directory
    :param training_script_path: Training script path, default: train.py
    """
    with TUI(
            f"Running a custom training job on Vertex AI for '{model_config.name}'",
            "Custom job finished successfully",
            "",
            "Custom training job failed",
            "",
    ) as tui:
        with StepTUI("Training on Vertex AI"):
            with SubStepTUI("Running a custom training job") as sub_step:
                sub_step.set_dirty()
                CustomJob.from_local_script(
                    display_name=f"{model_config.name}-custom-training",
                    script_path=training_script_path,
                    container_uri=model_config.training_container_image_uri,
                    requirements=requirements,
                    args=training_script_args,
                    replica_count=1,
                    project=gcp_config.project_id,
                    location=gcp_config.region,
                    staging_bucket=staging_bucket,
                    environment_variables={"RUNNING_ON_VERTEX": "True"}
                ).run()
            with SubStepTUI("Fetching the results"):
                client = storage.Client(project=gcp_config.project_id)
                metrics = json.loads(
                    storage.Blob.from_string(
                        os.path.join(output_dir, "metrics.json"),
                        client
                    ).download_as_bytes()
                )

                for metric in metrics:
                    _run.log_scalar(metric, metrics[metric])
        with StepTUI("Creating trained model"):
            with SubStepTUI("Creating trained model on Vertex AI") as sub_step:
                sub_step.set_dirty()
                model = Model.upload(
                    display_name=model_config.name,
                    project=gcp_config.project_id,
                    location=gcp_config.region,
                    serving_container_image_uri=model_config.serving_container_image_uri,
                    artifact_uri=output_dir,
                )
            with SubStepTUI("Saving results locally"):
                with open("trained_model.json", "w") as f:
                    f.write(to_json(TrainedModel.from_vertex_model(model)))


def vertex_wrapper(config: EdgeConfig, state: EdgeState, requirements: Optional[List[str]] = None):
    if requirements is None:
        requirements = []

    training_script_path = inspect.getframeinfo(sys._getframe(1)).filename

    def decorator(func):
        def inner(is_vertex: bool, *args, **kwargs):
            if is_vertex:
                if kwargs["model_name"] not in config.models:
                    print(f"Model '{kwargs['model_name']}' has not been initialised and therefore cannot be trained on "
                          f"Vertex AI. Initialise it by running `edge model init {kwargs['model_name']}`.")
                    sys.exit(1)

                # Define output bucket for Vertex
                staging_path, output_path = get_vertex_paths(config, state)

                kwargs["model_output_dir"] = output_path
                kwargs["is_vertex"] = False

                sacred_params = to_sacred_params_for_vertex(kwargs)

                training_script_args = [f"'{x}'" for x in sacred_params]

                run_job_on_vertex(
                    kwargs["_run"],
                    config.models[kwargs["model_name"]],
                    config.google_cloud_project,
                    requirements=requirements + [
                        "vertex-edge @ git+https://github.com/fuzzylabs/vertex-edge.git@hello-world#egg=vertex-edge"
                    ],
                    training_script_args=["-p", "with"] + training_script_args,
                    staging_bucket=staging_path,
                    output_dir=output_path,
                    training_script_path=training_script_path
                )
            else:
                func(*args, **kwargs)

        sig = inspect.signature(func)
        params_dict = sig._parameters.copy()
        if "is_vertex" not in params_dict:
            new_params_dict = OrderedDict({
                "is_vertex": inspect.signature(inner)._parameters["is_vertex"]
            })
            for key, param in params_dict.items():
                new_params_dict[key] = param
            sig._parameters = new_params_dict
        inner.__signature__ = sig
        inner.__name__ = func.__name__
        inner.__module__ = func.__module__

        return inner

    return decorator


def get_config_and_state() -> (Optional[EdgeConfig], Optional[EdgeState]):
    if os.environ.get("RUNNING_ON_VERTEX"):
        return None, None
    config = EdgeConfig.load(get_default_config_path_from_model(inspect.getframeinfo(sys._getframe(1)).filename))
    state = EdgeState.load(config)
    return config, state
