import os


def get_model_path(model_name: str):
    return f"models/{model_name}"


def get_model_dvc_pipeline(model_name: str):
    return os.path.join(get_model_path(model_name), "dvc.yaml")


def get_vertex_model_json(model_name: str):
    return os.path.join(get_model_path(model_name), "vertex_model.json")

