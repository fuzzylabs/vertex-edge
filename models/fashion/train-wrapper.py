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
from edge.training.sacred import to_sacred_params_for_vertex
from edge.training.training import run_job_on_vertex, TrainedModel
from edge.training.utils import wrap_open, get_vertex_paths

_config = EdgeConfig.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../edge.yaml"))
state = EdgeState.load(_config)

ex = Experiment("fashion-mnist-model-training")
track_experiment(_config, state, ex)


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


def vertex_wrapper(requirements: Optional[List[str]] = None):
    if requirements is None:
        requirements = []

    def decorator(func):
        def inner(is_vertex: bool, *args, **kwargs):
            if is_vertex:
                training_script_args = [f"'{x}'" for x in to_sacred_params_for_vertex(kwargs)]

                # Define output bucket for Vertex
                staging_path, output_path, metrics_path = get_vertex_paths(_config, state)

                run_job_on_vertex(
                    kwargs["_run"],
                    _config.models[kwargs["model_name"]],
                    _config.google_cloud_project,
                    requirements=requirements,
                    training_script_args=[" ".join(["with"] + training_script_args)],
                    staging_bucket=staging_path,
                    metrics_gs_link=metrics_path,
                    output_dir=output_path,
                    training_script_path=os.path.abspath(__file__)
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

        return inner

    return decorator


@ex.automain
@vertex_wrapper(requirements=[
    "google-cloud-storage==1.38.0",
    "dill==0.3.4",
    "scipy==1.6.3",
    "vertex-edge @ git+https://github.com/fuzzylabs/vertex-edge.git@generalised-training#egg=vertex-edge"
])
def main(
        _run: Experiment,
        params,
        model_name: str,
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
