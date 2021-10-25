import os
import joblib
import json
from serde.json import to_json

from edge.training.utils import wrap_open
from edge.training.training import TrainedModel


def save_results(model, metrics: dict, model_output_dir: str):
    with wrap_open(os.path.join(model_output_dir, "model.joblib"), "wb") as f:
        joblib.dump(model, f)

    with wrap_open(os.path.join(model_output_dir, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    with open("trained_model.json", "w") as f:
        f.write(to_json(TrainedModel.from_local_model()))
