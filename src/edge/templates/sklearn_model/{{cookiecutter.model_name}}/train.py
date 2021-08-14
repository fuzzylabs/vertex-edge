from edge.training.training import *
from edge.training.sklearn.utils import save_results
from edge.sacred import track_experiment
from sacred import Experiment

_config, state = get_config_and_state()
ex = Experiment("{{cookiecutter.model_name}}-model-training", save_git_info=False)

@ex.config
def cfg():
    # Add your config here
    model_name = "{{cookiecutter.model_name}}"
    is_vertex = False

@ex.automain
@vertex_wrapper(_config, state)
def run(_run,
        strategy,
        model_output_dir="./",
):
    # Add your model training code ehre

    metrics = {
        "score": # Add model score here
    }

    save_results(dummy_clf, metrics, model_output_dir)
