import os
import sys
import abc
import inspect
import logging
from typing import Optional, Any

from sacred import Experiment
from sacred.observers import MongoObserver
from google.cloud import secretmanager_v1
from google.cloud.aiplatform import CustomJob

from edge.training.utils import get_vertex_paths

logging.basicConfig(level = logging.INFO)

"""
TODO: These are helper functions that need to be moved elsewhere during refactoring
"""
import edge.path
from edge.state import EdgeState
from edge.config import ModelConfig, GCProjectConfig, EdgeConfig

# TODO: should this be here? Need dependency injection
def get_connection_string(project_id: str, secret_id: str) -> str:
    client = secretmanager_v1.SecretManagerServiceClient()
    secret_name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(name=secret_name)
    return response.payload.data.decode("UTF-8")

# TODO: Move this somewhere else
def get_config() -> EdgeConfig:
    # TODO: This looks error-prone
    config = EdgeConfig.load(edge.path.get_default_config_path_from_model(inspect.getframeinfo(sys._getframe(1)).filename))

    # TODO: Separate
    #state = EdgeState.load(config)

    return config

def get_state(config: EdgeConfig) -> EdgeState:
    return EdgeState.load(config)

"""
A Trainer encapsulates a model training script and its associated MLOps lifecycle

TODO: Explain why it has been built in this way. Sacred forces us into this pattern, but at least we hide it from the user.
TOOD: How much can we abstract this? What if Sacred is replaced with something else?
TODO: How can we be even better at handling experiment config?
"""
class Trainer():
    experiment = None
    parameters = {}
    edge_config = {}
    edge_state = {}
    name = None
    pip_requirements = [
        "sklearn",
        "vertex-edge @ git+https://github.com/fuzzylabs/vertex-edge.git@release/v0.2.0"
    ]
    vertex_training_image = "europe-docker.pkg.dev/cloud-aiplatform/training/scikit-learn-cpu.0-23:latest"
    vertex_training_bucket = None
    output_path = None # TODO: not used yet
    script_path = __file__

    # TODO: let the user choose from auto-inferred config and directly-specified config
    def __init__(self, name: str):
        self.name = name
        self.edge_config = get_config()
        self.edge_state = get_state(self.edge_config)

        self.vertex_training_bucket, self.output_path = get_vertex_paths(self.edge_config, self.edge_state)

        # TODO: Restore Git support
        self.experiment = Experiment(name, save_git_info=False)

        mongo_connection_string = get_connection_string(
            self.edge_config.google_cloud_project.project_id,
            self.edge_config.experiments.mongodb_connection_string_secret
        )

        self.experiment.observers.append(MongoObserver(mongo_connection_string))
        @self.experiment.main
        def ex_noop_main(c):
            pass


    @abc.abstractmethod
    def main(self):
        # TODO: A more user-friendly message
        raise NotImplementedError("The main method for this trainer has not been implemented")

    def set_parameter(self, key: str, value: Any):
        self.parameters[key] = value

    """
    Executes the training script and tracks experiment details
    """
    # TODO: Instead of on_vertex, have a target, which can be various things
    # TODO: What's the best way to distinguish local and vertex runs? this way is a bit confusing
    def run(self):
        on_vertex = os.environ.get("RUN_ON_VERTEX")

        if on_vertex:
            logging.info("Deploying training job to Vertex")
            self._run_on_vertex()
        else:
            logging.info("Executing model trainer")
            self._run_locally()

    def _run_locally(self):
        ex_run = self.experiment._create_run()
        result = self.main()
        parameters = self.parameters | ex_run.config

        ex_run.log_scalar("score", result)

        logging.info(f"RESULT {result}")
        logging.info(f"PARAMETERS {parameters}")

        ex_run(parameters)

    def _run_on_vertex(self):
        logging.info(f"""Deploying to vertex with the following:
            name: {self.name}
            script_path: {self.script_path}
            container: {self.vertex_training_image}
            requirements: {self.pip_requirements}
            project: {self.edge_config.google_cloud_project.project_id}
            location: {self.edge_config.google_cloud_project.region}
            staging_bucket: {self.vertex_training_bucket}
            """)

        CustomJob.from_local_script(
            display_name=f"{self.name}-custom-training",
            script_path=self.script_path,
            container_uri=self.vertex_training_image,
            requirements=self.pip_requirements,
            #args=training_script_args,
            replica_count=1,
            project=self.edge_config.google_cloud_project.project_id,
            location=self.edge_config.google_cloud_project.region,
            staging_bucket=self.vertex_training_bucket,
            environment_variables={"RUN_ON_VERTEX": "False"}
        ).run()
