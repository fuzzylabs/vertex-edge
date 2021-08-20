import abc
from sacred import Experiment
from sacred.observers import MongoObserver
from google.cloud import secretmanager_v1

class Trainer():
    ex = None

    # TODO: should this be here?
    def get_connection_string(self, project_id: str, secret_id: str) -> str:
        client = secretmanager_v1.SecretManagerServiceClient()
        secret_name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(name=secret_name)
        return response.payload.data.decode("UTF-8")

    def __init__(self, name: str):
        self.ex = Experiment(name, save_git_info=True)

        # How should this be injected?
        project_id = "hello-world-vertex"
        secret_id = "sacred-mongodb-connection-string"
        mongo_connection_string = self.get_connection_string(project_id, secret_id)
        self.ex.observers.append(MongoObserver(mongo_connection_string))

        @self.ex.main
        def ex_noop_main(config):
            pass

        # TODO: this is just here for testing - need to pass params through from user script
        self.ex.add_config(
            {  
                "some_parameter": 42
            }
        )

    @abc.abstractmethod
    def main(self):
        raise NotImplementedError("The main method for this trainer has not been implemented")

    def run(self):
        ex_run = self.ex._create_run()
        result = self.main()

        ex_run.log_scalar("score", result)

        print(f"RESULT {result}")
        print(f"CONFIG {ex_run.config}")

        ex_run(ex_run.config)
