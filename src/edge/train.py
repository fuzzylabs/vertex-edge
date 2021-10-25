import os
import sys
import abc
import uuid
import inspect
import logging
from typing import Optional, Any
from enum import Enum

from sacred import Experiment
from sacred.observers import MongoObserver
from google.cloud import secretmanager_v1
from google.cloud.aiplatform import CustomJob

import edge.path
#from edge.state import EdgeState
from edge.config import EdgeConfig

logging.basicConfig(level = logging.INFO)

class TrainingTarget(Enum):
    LOCAL = "local"
    VERTEX = "vertex"

"""
A Trainer encapsulates a model training script and its associated MLOps lifecycle

TODO: Explain why it has been built in this way. Sacred forces us into this pattern, but at least we hide it from the user.
TOOD: How much can we abstract this? What if Sacred is replaced with something else?
TODO: How can we be even better at handling experiment config?
"""
class Trainer():
    # TODO: group together experiment variables and Vertex variables. Note when target is local, we don't need Vertex values
    experiment = None
    parameters = {}
    edge_config = None
    #edge_state = None
    name = None
    pip_requirements = [
        "sklearn",
        "vertex-edge @ git+https://github.com/fuzzylabs/vertex-edge.git@release/v0.2.0"
    ]
    vertex_training_image = "europe-docker.pkg.dev/cloud-aiplatform/training/scikit-learn-cpu.0-23:latest"
    vertex_staging_path = None
    #vertex_output_path = None
    script_path = None
    mongo_connection_string = None
    target = TrainingTarget.LOCAL

    def __init__(self, name: str):
        self.name = name

        # We need the path to the training script itself
        self.script_path = inspect.getframeinfo(sys._getframe(1)).filename

        # Determine our target training environment
        if os.environ.get("RUN_ON_VERTEX") == "True":
            logging.info("Target training environment is Vertex")
            self.target = TrainingTarget.VERTEX
        else:
            logging.info("Target training environment is Local")
            self.target = TrainingTarget.LOCAL

        # Load the Edge configuration from the appropriate source
        # TODO: Document env var
        if os.environ.get("EDGE_CONFIG"):
            logging.info("Edge config will be loaded from environment variable EDGE_CONFIG_STRING")
            self.edge_config = self._decode_config_string(os.environ.get("EDGE_CONFIG"))
        else:
            logging.info("Edge config will be loaded from edge.yaml")
            # TODO: This isn't very stable. We should search for the config file.
            self.edge_config = EdgeConfig.load(edge.path.get_default_config_path_from_model(inspect.getframeinfo(sys._getframe(1)).filename))

        # Load the Edge state
        #self.edge_state = EdgeState.load(self.edge_config)
        #logging.info(f"Edge state: {self.edge_state}")

        # Determine correct values for running on Vertex
        self.vertex_staging_path = "gs://" + os.path.join(
            self.edge_config.storage_bucket.bucket_name,
            self.edge_config.storage_bucket.vertex_jobs_directory
        )
        #self.vertex_output_path = os.path.join(self.vertex_training_path, str(uuid.uuid4()))

        # Set up experiment tracking for this training job
        # TODO: Restore Git support
        # TODO: If training target is Vertex, we don't need to init an experiment
        # TODO: Experiment initialisation in its own function (but *must* be called during construction)
        self.experiment = Experiment(name, save_git_info=False)

        # TODO: Document env var
        if os.environ.get("MONGO_CONNECTION_STRING"):
            self.mongo_connection_string = os.environ.get("MONGO_CONNECTION_STRING")
        else:
            self.mongo_connection_string = self._get_mongo_connection_string()

        self.experiment.observers.append(MongoObserver(self.mongo_connection_string))

        @self.experiment.main
        def ex_noop_main(c):
            pass

    """
    To be implemented by data scientist
    """
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
        if self.target == TrainingTarget.VERTEX:
            self._run_on_vertex()
        else:
            self._run_locally()

    def _run_locally(self):
        ex_run = self.experiment._create_run()
        result = self.main()
        # TODO: Python 3.9 has a new syntax for merging maps, but Vertex doesn't run 3.9 yet so we can't use it. See https://www.python.org/dev/peps/pep-0584/
        parameters = {**self.parameters, **ex_run.config}

        ex_run.log_scalar("score", result)
        ex_run(parameters)

    def _run_on_vertex(self):
        environment_variables = {
            "RUN_ON_VERTEX": "False",
            "EDGE_CONFIG": self._get_encoded_config(),
            "MONGO_CONNECTION_STRING": self.mongo_connection_string
        }

        CustomJob.from_local_script(
            display_name=f"{self.name}-custom-training",
            script_path=self.script_path,
            container_uri=self.vertex_training_image,
            requirements=self.pip_requirements,
            #args=training_script_args,
            replica_count=1,
            project=self.edge_config.google_cloud_project.project_id,
            location=self.edge_config.google_cloud_project.region,
            staging_bucket=self.vertex_staging_path,
            environment_variables=environment_variables
        ).run()

    def _get_encoded_config(self) -> str:
        return str(self.edge_config).replace("\n", "\\n")

    def _decode_config_string(self, s: str) -> EdgeConfig:
        return EdgeConfig.from_string(s.replace("\\n", "\n"))

    def _get_mongo_connection_string(self) -> str:
        # TODO: If experiment tracker isn't initialised, this fails
        client = secretmanager_v1.SecretManagerServiceClient()
        secret_name = f"projects/{self.edge_config.google_cloud_project.project_id}/secrets/{self.edge_config.experiments.mongodb_connection_string_secret}/versions/latest"
        response = client.access_secret_version(name=secret_name)
        return response.payload.data.decode("UTF-8")
