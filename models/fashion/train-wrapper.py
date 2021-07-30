import inspect
from collections import OrderedDict
from typing import List, Optional

import dill
import joblib
import json
import dvc.api
import yaml
import uuid
import os.path
from sacred import Experiment
from serde.json import to_json
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score
from edge.sacred import track_experiment
from edge.config import EdgeConfig
from edge.state import EdgeState
from edge.training.sacred import to_sacred_params_for_vertex, to_sacred_with_statement
from edge.training.training import run_job_on_vertex, TrainedModel

_config = EdgeConfig.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../edge.yaml"))
state = EdgeState.load(_config)

ex = Experiment("fashion-mnist-model-training")
track_experiment(_config, state, ex)


def get_vertex_paths():
    staging_path = os.path.join(state.storage.bucket_path, _config.storage_bucket.vertex_jobs_directory)
    output_path = os.path.join(staging_path, str(uuid.uuid4()))

    metrics_path = os.path.join(output_path, "metrics.json")
    return staging_path, output_path, metrics_path


def wrap_open(path: str, mode: str = "r"):
    if path.startswith("gs://"):
        from google.cloud import storage
        from google.cloud.storage.blob import Blob

        client = storage.Client()

        return Blob.from_string(path, client).open(mode=mode)
    else:
        return open(path, mode=mode)


def train_model(train_dataset, n_neighbors):
    (train_images, train_labels) = train_dataset

    # Define the simplest SVC model
    model = KNeighborsClassifier(n_neighbors=n_neighbors)
    print(model)

    # Train model
    model.fit(train_images, train_labels)
    return model


def test_model(model, test_dataset):
    (test_images, test_labels) = test_dataset

    predicted_labels = model.predict(test_images)
    accuracy = accuracy_score(list(test_labels), predicted_labels)
    print("Accuracy:", accuracy)
    return {"accuracy": accuracy}


def load_datasets(train_set_path, test_set_path):
    with wrap_open(train_set_path, "rb") as f:
        train_set = dill.load(f)
    with wrap_open(test_set_path, "rb") as f:
        test_set = dill.load(f)

    return train_set, test_set


def save_results(model, metrics, model_output_dir, metrics_output_path):
    with wrap_open(os.path.join(model_output_dir, "model.joblib"), "wb") as f:
        joblib.dump(model, f)

    with wrap_open(metrics_output_path, "w") as f:
        json.dump(metrics, f, indent=2)


@ex.config
def config():
    params = yaml.safe_load(open("params.yaml"))["train"]
    print(type(params), params)
    is_vertex = params["is_vertex"]

    model_name = "fashion"

    # Get dataset links
    train_uri = dvc.api.get_url("data/fashion-mnist/train.pickle")
    test_uri = dvc.api.get_url("data/fashion-mnist/test.pickle")

    # Define local defaults
    model_dir = "./"
    model_metrics_path = "./metrics.json"

    # Define output bucket for Vertex
    staging_path, output_path, metrics_path = get_vertex_paths()


def vertex_wrapper(func, requirements: Optional[List[str]] = None):
    if requirements is None:
        requirements = []

    def inner(is_vertex: bool, *args, **kwargs):
        if is_vertex:
            print("TODO Run on vertex")
            training_script_args = to_sacred_params_for_vertex(kwargs)
            print("with ", " ".join(training_script_args))
            # run_job_on_vertex(
            #     kwargs["_run"],
            #     _config.models[kwargs["model_name"]],
            #     _config.google_cloud_project,
            #     requirements=requirements,
            #     training_script_args=[
            #         "--model-dir",
            #         output_path,
            #         "--model-metrics-path",
            #         metrics_path,
            #         "--n-neigbours",
            #         str(params["n_neighbours"]),
            #         train_uri,
            #         test_uri,
            #     ],
            #     staging_bucket=staging_path,
            #     metrics_gs_link=metrics_path,
            #     output_dir=output_path,
            # )
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

    return inner


@ex.automain
@vertex_wrapper
def main(
        _run: Experiment,
        params,
        train_uri: str,
        test_uri: str,
        model_dir: str,
        model_metrics_path: str
):
    print("Load")
    train_set, test_set = load_datasets(train_uri, test_uri)
    print("Train")
    model = train_model(train_set, params["n_neighbours"])
    print("Test")
    metrics = test_model(model, test_set)
    print("Save")
    save_results(model, metrics, model_dir, model_metrics_path)
    with open("trained_model.json", "w") as f:
        f.write(to_json(TrainedModel.from_local_model()))
