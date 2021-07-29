import json
from google.cloud.aiplatform import CustomJob, Model
from google.cloud import storage
import dvc.api
import yaml
import uuid
import os.path
from sacred import Experiment
from edge.sacred import track_experiment
from edge.config import EdgeConfig
from edge.state import EdgeState

_config = EdgeConfig.load_default()
state = EdgeState.load(_config)

ex = Experiment("fashion-mnist-model-training")
track_experiment(_config, state, ex)


@ex.config
def config():
    print("Preparing job to run on Vertex AI")
    params = yaml.safe_load(open("params.yaml"))["train"]

    # Get dataset links
    train_uri = dvc.api.get_url("data/fashion-mnist/train.pickle")
    test_uri = dvc.api.get_url("data/fashion-mnist/test.pickle")

    # Define output bucket
    vertex_dir = os.path.join(state.storage.bucket_path, _config.storage_bucket.vertex_jobs_directory)
    output_dir = os.path.join(vertex_dir, str(uuid.uuid4()))

    model_gs_link = os.path.join(output_dir, "model.joblib")
    metrics_gs_link = os.path.join(output_dir, "metrics.json")

    image_tag = os.environ.get("IMAGE_TAG")
    if image_tag is None:
        image_tag = "latest"


@ex.automain
def main(
    _run,
    params,
    train_uri: str,
    test_uri: str,
    vertex_dir: str,
    output_dir: str,
    metrics_gs_link: str,
    image_tag: str,
):
    print("Running the job")
    # Run job
    CustomJob.from_local_script(
        display_name="Fashion MNIST Naive Bayes",
        script_path="train.py",
        container_uri="europe-docker.pkg.dev/cloud-aiplatform/training/scikit-learn-cpu.0-23:latest",
        requirements=[
            "scikit-learn==0.23.1",
            "google-cloud-storage==1.38.0",
            "dill==0.3.4",
            "scipy==1.6.3",
        ],
        args=[
            "--model-dir",
            output_dir,
            "--model-metrics-path",
            metrics_gs_link,
            "--n-neigbours",
            str(params["n_neighbours"]),
            train_uri,
            test_uri,
        ],
        replica_count=1,
        project=_config.google_cloud_project.project_id,
        location=_config.google_cloud_project.region,
        staging_bucket=vertex_dir,
    ).run()

    # Get results back
    print("Fetching the results")  # TODO see options for linking from gs, instead of downloading locally

    client = storage.Client(project=_config.google_cloud_project.project_id)
    metrics = json.loads(storage.Blob.from_string(metrics_gs_link, client).download_as_bytes())

    for metric in metrics:
        _run.log_scalar(metric, metrics[metric])

    # Create model on Vertex
    print("Creating model")
    serving_container_image_uri = (
        f"{_config.models['fashion'].prediction_server_image}:{image_tag}"
    )
    model = Model.upload(
        display_name=_config.models["fashion"].name,
        project=_config.google_cloud_project.project_id,
        location=_config.google_cloud_project.region,
        serving_container_image_uri="europe-docker.pkg.dev/cloud-aiplatform/prediction/sklearn-cpu.0-23:latest",
        artifact_uri=output_dir,
    )

    with open("vertex_model.json", "w") as f:
        json.dump(
            {
                "model_name": model.resource_name,
            },
            f,
        )
