import subprocess
import dvc
import os
from edge.config import EdgeConfig
from edge.state import StorageBucketState


def dvc_init():
    print("## Initialising DVC")
    if os.path.exists(".dvc") and os.path.isdir(".dvc"):
        print("DVC is already initialised")
    else:
        try:
            subprocess.check_output("dvc init", shell=True)
        except subprocess.CalledProcessError as e:
            print(e.output)
            print("Error occurred while initialising DVC")
            exit(1)
        print("DVC is initialised")


def dvc_remote_exists(path: str) -> (bool, bool):
    try:
        remotes_raw = subprocess.check_output("dvc remote list", shell=True).decode("utf-8")
        remotes = [x.split("\t") for x in remotes_raw.strip().split("\n") if len(x.split("\t")) == 2]
        for remote in remotes:
            if remote[0] == "storage":
                if remote[1] == path:
                    return True, True
                else:
                    return True, False
        return False, False
    except subprocess.CalledProcessError as e:
        print(e.output)
        print("Error occurred while adding remote storage to DVC")
        exit(1)


def dvc_add_remote(path: str):
    try:
        print(f"## Adding {path} to DVC remotes")
        storage_exists, correct_path = dvc_remote_exists(path)
        if storage_exists:
            if correct_path:
                print(f"{path} has already been added")
            else:
                print(f"modifying existing storage to {path}")
                subprocess.check_output(f"dvc remote modify storage url {path}", shell=True)
        else:
            subprocess.check_output(f"dvc remote add storage {path}", shell=True)
    except subprocess.CalledProcessError as e:
        print(e.output)
        print("Error occurred while adding remote storage to DVC")
        exit(1)


def setup_dvc(_config: EdgeConfig, storage_state: StorageBucketState):
    print("# Setting up DVC")
    dvc_init()
    storage_path = os.path.join(storage_state.bucket_path, _config.storage_bucket.dvc_store_directory)
    dvc_add_remote(storage_path)