import json
import os.path
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score
import argparse
import dill
import joblib


def wrap_open(path: str, mode: str = "r"):
    if path.startswith("gs://"):
        from google.cloud import storage
        from google.cloud.storage.blob import Blob

        client = storage.Client()

        return Blob.from_string(path, client).open(mode=mode)
    else:
        return open(path, mode=mode)


def train_model(train_dataset, n_neighbors):
    (train_images, train_labels) = train_dataset

    # Define the simplest SVC model
    model = KNeighborsClassifier(n_neighbors=n_neighbors)
    print(model)

    # Train model
    model.fit(train_images, train_labels)
    return model


def test_model(model, test_dataset):
    (test_images, test_labels) = test_dataset

    predicted_labels = model.predict(test_images)
    accuracy = accuracy_score(list(test_labels), predicted_labels)
    print("Accuracy:", accuracy)
    return {"accuracy": accuracy}


def load_datasets(train_set_path, test_set_path):
    with wrap_open(train_set_path, "rb") as f:
        train_set = dill.load(f)
    with wrap_open(test_set_path, "rb") as f:
        test_set = dill.load(f)

    return train_set, test_set


def save_results(model, metrics, model_output_dir, metrics_output_path):
    with wrap_open(os.path.join(model_output_dir, "model.joblib"), "wb") as f:
        joblib.dump(model, f)

    with wrap_open(metrics_output_path, "w") as f:
        json.dump(metrics, f, indent=2)


if __name__ == "__main__":
    """
    Assumptions:
     
    * the script takes two datasets (training and testing)
    * the script takes model-metrics-path as the parameter and outputs to `./metrics.json` by default
    * the script saves all the relevant metrics to model-metrics-path
    * the script produces `model.joblib` artifact and puts it to model-dir
    * the script accepts local paths and gs:// paths
    """
    parser = argparse.ArgumentParser("Train a model")
    parser.add_argument("train_set_path")
    parser.add_argument("test_set_path")
    parser.add_argument("--n-neigbours", dest="n_neighbours", default=1, type=int)
    parser.add_argument("--model-dir", dest="model_dir", default=os.getenv("AIP_MODEL_DIR"))
    parser.add_argument("--model-metrics-path", dest="model_metrics_path", default="metrics.json")

    args = parser.parse_args()
    print(args)

    print("Load")
    train_set, test_set = load_datasets(args.train_set_path, args.test_set_path)
    print("Train")
    model = train_model(train_set, args.n_neighbours)
    print("Test")
    metrics = test_model(model, test_set)
    print("Save")
    save_results(model, metrics, args.model_dir, args.model_metrics_path)
