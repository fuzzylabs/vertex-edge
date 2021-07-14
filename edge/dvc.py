import glob
import subprocess
from typing import Optional

import dvc
import os
import shutil
from edge.config import EdgeConfig
from edge.state import StorageBucketState


def dvc_exists() -> bool:
    return os.path.exists(".dvc") and os.path.isdir(".dvc")


def dvc_init():
    if dvc_exists():
        return
    print("## Initialising DVC")
    try:
        subprocess.check_output("dvc init", shell=True)
    except subprocess.CalledProcessError as e:
        print(e.output)
        print("Error occurred while initialising DVC")
        exit(1)
    print("DVC is initialised")


def dvc_destroy():
    print("## Deleting DVC configuration [.dvc]")
    shutil.rmtree(".dvc")
    print("## Deleting DVC data [data/fashion-mnist/*.dvc]")
    for f in glob.glob("data/fashion-mnist/*.dvc"):
        os.remove(f)
    print("## Deleting pipeline lock file [models/pipelines/fashion/dvc.lock]")
    if os.path.exists("models/pipelines/fashion/dvc.lock"):
        os.remove("models/pipelines/fashion/dvc.lock")
    print("DVC is destroyed")


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


def get_dvc_storage_path() -> Optional[str]:
    try:
        remotes_raw = subprocess.check_output("dvc remote list", shell=True).decode("utf-8")
        remotes = [x.split("\t") for x in remotes_raw.strip().split("\n") if len(x.split("\t")) == 2]
        for remote in remotes:
            if remote[0] == "storage":
                return remote[1].strip()
        return None
    except subprocess.CalledProcessError as e:
        print(e.output)
        print("Error occurred while getting DVC remote storage path")
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
                subprocess.check_output(f"dvc remote modify storage url {path} && dvc remote default storage", shell=True)
        else:
            subprocess.check_output(f"dvc remote add storage {path} && dvc remote default storage", shell=True)
    except subprocess.CalledProcessError as e:
        print(e.output)
        print("Error occurred while adding remote storage to DVC")
        exit(1)


def setup_dvc(_config: EdgeConfig, storage_state: StorageBucketState):
    storage_path = os.path.join(storage_state.bucket_path, _config.storage_bucket.dvc_store_directory)
    print("# Setting up DVC")
    print("## Checking if DVC is already initialised")
    exists = dvc_exists()
    if exists:
        print("DVC is initialised")
        if storage_path != get_dvc_storage_path():
            print(
                f"DVC remote storage does not match vertex:edge config: expected -- {storage_path}, "
                f"got -- {get_dvc_storage_path()}"
            )
            print("WARNING: To use the new Google Storage bucket it is advised to destroy DVC repository, "
                  "and initialise from scratch.")
            choice = None
            while choice not in ["y", "n"]:
                choice = input("Do you want to destroy DVC and initialise it from scratch (y/n)? [n]: ").strip().lower()
                if choice == "":
                    choice = "n"

            if choice == "y":
                dvc_destroy()
    else:
        print("DVC is not initialised")
    dvc_init()
    dvc_add_remote(storage_path)
