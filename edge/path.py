import os


def get_model_path():
    return "models/fashion"


def get_model_dvc_pipeline():
    return os.path.join(get_model_path(), "dvc.yaml")
