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
from google.cloud.aiplatform import Model, CustomJob

import edge.path
#from edge.state import EdgeState
from edge.config import EdgeConfig
from edge.exception import EdgeException

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
    experiment_run = None
    edge_config = None
    #edge_state = None
    name = None
    # TODO: Remove hard-coded Git link
    pip_requirements = [
        "vertex-edge @ git+https://github.com/fuzzylabs/vertex-edge.git@release/v0.2.0"
    ]
    vertex_staging_path = None
    vertex_output_path = None
    script_path = None
    mongo_connection_string = None
    target = TrainingTarget.LOCAL
    model_config = None
    model_id = None

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

        # Extract the model configuration and check if the model has been initialised
        if name in self.edge_config.models:
            self.model_config = self.edge_config.models[name]
        else:
            raise EdgeException(f"Model with name {name} could not be found in Edge config. Perhaps it hasn't been initialised")

        # Load the Edge state
        #self.edge_state = EdgeState.load(self.edge_config)
        #logging.info(f"Edge state: {self.edge_state}")

        if os.environ.get("MODEL_ID"):
            self.model_id = os.environ.get("MODEL_ID")
        else:
            self.model_id = uuid.uuid4()
        
        # Determine correct paths for Vertex running
        self.vertex_staging_path = "gs://" + os.path.join(
            self.edge_config.storage_bucket.bucket_name,
            self.edge_config.storage_bucket.vertex_jobs_directory
        )
        self.vertex_output_path = os.path.join(self.vertex_staging_path, str(self.model_id))

        # Set up experiment tracking for this training job
        # TODO: Restore Git support
        # TODO: If training target is Vertex, we don't need to init an experiment
        # TODO: Experiment initialisation in its own function (but *must* be called during construction)
        self.experiment = Experiment(name, save_git_info=True)

        # TODO: Document env var
        if os.environ.get("MONGO_CONNECTION_STRING"):
            self.mongo_connection_string = os.environ.get("MONGO_CONNECTION_STRING")
        else:
            self.mongo_connection_string = self._get_mongo_connection_string()

        if self.mongo_connection_string is not None:
            self.experiment.observers.append(MongoObserver(self.mongo_connection_string))
        else:
            logging.info("Experiment tracker has not been initialised")

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
        self.experiment_run.config[key] = value

    def get_parameter(self, key: str) -> Any:
        return self.experiment_run.config[key]

    def log_scalar(self, key: str, value: Any):
        self.experiment_run.log_scalar(key, value)

    def get_model_save_path(self):
        # TODO: Support local paths
        return self.vertex_output_path

    """
    Executes the training script and tracks experiment details
    """
    # TODO: Instead of on_vertex, have a target, which can be various things
    # TODO: What's the best way to distinguish local and vertex runs? this way is a bit confusing
    def run(self):
        if self.target == TrainingTarget.VERTEX:
            self._run_on_vertex()
            self._create_model_on_vertex()
        else:
            self._run_locally()

    def _run_locally(self):
        self.experiment_run = self.experiment._create_run()
        result = self.main()

        self.experiment_run.log_scalar("score", result)
        self.experiment_run({})

    def _run_on_vertex(self):
        environment_variables = {
            "RUN_ON_VERTEX": "False",
            "EDGE_CONFIG": self._get_encoded_config(),
            "MODEL_ID": self.model_id
        }

        if self.mongo_connection_string is not None:
            environment_variables["MONGO_CONNECTION_STRING"] = self.mongo_connection_string

        CustomJob.from_local_script(
            display_name=f"{self.name}-custom-training",
            script_path=self.script_path,
            container_uri=self.model_config.training_container_image_uri,
            requirements=self.pip_requirements,
            #args=training_script_args,
            replica_count=1,
            project=self.edge_config.google_cloud_project.project_id,
            location=self.edge_config.google_cloud_project.region,
            staging_bucket=self.vertex_staging_path,
            environment_variables=environment_variables
        ).run()

    def _create_model_on_vertex(self):
        model = Model.upload(
            display_name=self.name,
            project=self.edge_config.google_cloud_project.project_id,
            location=self.edge_config.google_cloud_project.region,
            serving_container_image_uri=self.model_config.serving_container_image_uri,
            artifact_uri=self.get_model_save_path()
        )

    def _get_encoded_config(self) -> str:
        return str(self.edge_config).replace("\n", "\\n")

    def _decode_config_string(self, s: str) -> EdgeConfig:
        return EdgeConfig.from_string(s.replace("\\n", "\n"))

    def _get_mongo_connection_string(self) -> str:
        # Try to get the Mongo connection string, if available
        try:
            client = secretmanager_v1.SecretManagerServiceClient()
            secret_name = f"projects/{self.edge_config.google_cloud_project.project_id}/secrets/{self.edge_config.experiments.mongodb_connection_string_secret}/versions/latest"
            response = client.access_secret_version(name=secret_name)
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            return None
