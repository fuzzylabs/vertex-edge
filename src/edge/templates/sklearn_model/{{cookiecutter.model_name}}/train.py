from edge.training.training import *
from edge.training.sklearn.utils import save_results
from edge.sacred import track_experiment

from sacred import Experiment

import numpy as np
from sklearn.dummy import DummyClassifier


_config, state = get_config_and_state()

# Start Sacred experiment
ex = Experiment("{{cookiecutter.model_name}}-model-training", save_git_info=False)

track_experiment(_config, state, ex)


@ex.config
def cfg():
    strategy = "most_frequent"
    model_name = "{{cookiecutter.model_name}}"
    is_vertex = False


@ex.automain
@vertex_wrapper(_config, state)
def run(
        _run,
        strategy,
        model_output_dir="./",
):
    X = np.array([-1, 1, 1, 1])
    y = np.array([0, 1, 1, 1])
    dummy_clf = DummyClassifier(strategy=strategy)
    dummy_clf.fit(X, y)

    _run.log_scalar("score", dummy_clf.score(X, y))

    metrics = {
        "score": dummy_clf.score(X, y)
    }

    save_results(dummy_clf, metrics, model_output_dir)
