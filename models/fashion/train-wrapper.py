import dvc.api
import yaml
import uuid
import os.path
from sacred import Experiment

from edge.sacred import track_experiment
from edge.config import EdgeConfig
from edge.state import EdgeState
from edge.training.training import run_job_locally, run_job_on_vertex

_config = EdgeConfig.load_default()
state = EdgeState.load(_config)

ex = Experiment("fashion-mnist-model-training")
track_experiment(_config, state, ex)


def get_vertex_paths():
    staging_path = os.path.join(state.storage.bucket_path, _config.storage_bucket.vertex_jobs_directory)
    output_path = os.path.join(staging_path, str(uuid.uuid4()))

    metrics_path = os.path.join(output_path, "metrics.json")
    return staging_path, output_path, metrics_path


def config_wrapper(func):
    __config = ex.config(func)
    print(__config)
    return __config


@config_wrapper
def config():
    params = yaml.safe_load(open("params.yaml"))["train"]

    is_local = params["is_local"]

    model_name = "fashion"

    # Get dataset links
    train_uri = dvc.api.get_url("data/fashion-mnist/train.pickle")
    test_uri = dvc.api.get_url("data/fashion-mnist/test.pickle")

    # Define output bucket
    staging_path, output_path, metrics_path = get_vertex_paths()


@ex.automain
def main(
    _run: Experiment,
    params,
    is_local: bool,
    model_name: str,
    train_uri: str,
    test_uri: str,
    staging_path: str,
    output_path: str,
    metrics_path: str,
):
    if is_local:
        run_job_locally(
            _run,
            _config.models[model_name],
            training_script_args=[
                "--model-dir",
                ".",
                "--n-neigbours",
                str(params["n_neighbours"]),
                train_uri,
                test_uri,
            ],
        )
    else:
        run_job_on_vertex(
            _run,
            _config.models[model_name],
            _config.google_cloud_project,
            requirements=[
                "scikit-learn==0.23.1",
                "google-cloud-storage==1.38.0",
                "dill==0.3.4",
                "scipy==1.6.3",
            ],
            training_script_args=[
                "--model-dir",
                output_path,
                "--model-metrics-path",
                metrics_path,
                "--n-neigbours",
                str(params["n_neighbours"]),
                train_uri,
                test_uri,
            ],
            staging_bucket=staging_path,
            metrics_gs_link=metrics_path,
            output_dir=output_path,
        )
