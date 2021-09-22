import os


def get_default_config_path():
    # TODO: Document env var
    path = os.environ.get("EDGE_CONFIG_PATH")
    if path is None:
        path = os.path.join(os.getcwd(), "edge.yaml")
    return path


def get_default_config_path_from_model(caller: str):
    path = os.environ.get("EDGE_CONFIG_PATH")
    if path is None:
        path = os.path.join(os.path.dirname(caller), "../../", "edge.yaml")
    return path


def get_model_path(model_name: str):
    return f"models/{model_name}"


def get_model_dvc_pipeline(model_name: str):
    return os.path.join(get_model_path(model_name), "dvc.yaml")


def get_vertex_model_json(model_name: str):
    return os.path.join(get_model_path(model_name), "trained_model.json")

