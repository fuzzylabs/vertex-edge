import glob
import subprocess
from typing import Optional

import os
import shutil
from edge.exception import EdgeException
from edge.tui import StepTUI, SubStepTUI, TUIStatus, qmark
import questionary


def dvc_exists() -> bool:
    return os.path.exists(".dvc") and os.path.isdir(".dvc")


def dvc_init():
    with StepTUI("Initialising DVC", emoji="🔨"):
        with SubStepTUI("Initialising DVC"):
            try:
                subprocess.check_output("dvc init", shell=True, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError as e:
                raise EdgeException("Unexpected error occurred while initialising DVC:\n{str(e)}")


def dvc_destroy():
    with StepTUI("Destroying DVC", emoji="🔥"):
        with SubStepTUI("Deleting DVC configuration [.dvc]"):
            shutil.rmtree(".dvc")
        with SubStepTUI("Deleting DVC data [data/fashion-mnist/*.dvc]"):
            for f in glob.glob("data/fashion-mnist/*.dvc"):
                os.remove(f)
        with SubStepTUI("Deleting pipeline lock file [models/pipelines/fashion/dvc.lock]"):
            if os.path.exists("models/pipelines/fashion/dvc.lock"):
                os.remove("models/pipelines/fashion/dvc.lock")


def dvc_remote_exists(path: str) -> (bool, bool):
    try:
        remotes_raw = subprocess.check_output("dvc remote list", shell=True, stderr=subprocess.DEVNULL).decode("utf-8")
        remotes = [x.split("\t") for x in remotes_raw.strip().split("\n") if len(x.split("\t")) == 2]
        for remote in remotes:
            if remote[0] == "storage":
                if remote[1] == path:
                    return True, True
                else:
                    return True, False
        return False, False
    except subprocess.CalledProcessError as e:
        raise EdgeException(f"Unexpected error occurred while adding remote storage to DVC:\n{str(e)}")


def get_dvc_storage_path() -> Optional[str]:
    try:
        remotes_raw = subprocess.check_output("dvc remote list", shell=True, stderr=subprocess.DEVNULL).decode("utf-8")
        remotes = [x.split("\t") for x in remotes_raw.strip().split("\n") if len(x.split("\t")) == 2]
        for remote in remotes:
            if remote[0] == "storage":
                return remote[1].strip()
        return None
    except subprocess.CalledProcessError as e:
        raise EdgeException(f"Unexpected error occurred while getting DVC remote storage path:\n{str(e)}")


def dvc_add_remote(path: str):
    with StepTUI("Configuring DVC remote storage", emoji="⚙️"):
        with SubStepTUI(f"Adding '{path}' as DVC remote storage URI") as sub_step:
            try:
                storage_exists, correct_path = dvc_remote_exists(path)
                if storage_exists:
                    if correct_path:
                        return
                    else:
                        sub_step.update(f"Modifying existing storage to {path}")
                        subprocess.check_output(
                            f"dvc remote modify storage url {path} && dvc remote default storage", shell=True,
                            stderr=subprocess.DEVNULL
                        )
                else:
                    subprocess.check_output(f"dvc remote add storage {path} && dvc remote default storage", shell=True,
                                            stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError as e:
                raise EdgeException(f"Unexpected error occurred while adding remote storage to DVC:\n{str(e)}")


def setup_dvc(bucket_path: str, dvc_store_directory: str):
    storage_path = os.path.join(bucket_path, dvc_store_directory)
    exists = False
    is_remote_correct = False
    to_destroy = False
    with StepTUI("Checking DVC configuration", emoji="🔍"):
        with SubStepTUI("Checking if DVC is already initialised") as sub_step:
            exists = dvc_exists()
            if not exists:
                sub_step.update(
                    message="DVC is not initialised",
                    status=TUIStatus.NEUTRAL
                )
        if exists:
            with SubStepTUI("Checking if DVC remote storage is configured") as sub_step:
                configured_storage_path = get_dvc_storage_path()
                is_remote_correct = storage_path == configured_storage_path
                if configured_storage_path is None:
                    sub_step.update(
                        f"DVC remote storage is not configured",
                        status=TUIStatus.NEUTRAL
                    )
                elif not is_remote_correct:
                    sub_step.update(
                        f"DVC remote storage does not match vertex:edge config",
                        status=TUIStatus.WARNING
                    )
                    sub_step.set_dirty()
                    sub_step.add_explanation(
                        f"DVC remote storage is configured to '{configured_storage_path}', "
                        f"but vertex:edge config expects '{storage_path}'. "
                        "This might mean that DVC has been already initialised to work with a different GCP "
                        "environment. If this is the case, we recommend to reinitialise DVC from scratch"
                    )
                    to_destroy = questionary.confirm(
                        "Do you want to destroy DVC and initialise it from scratch? (this action is destructive!)",
                        default=False,
                        qmark=qmark
                    ).ask()
                    if to_destroy is None:
                        raise EdgeException("Canceled by user")
        if to_destroy:
            dvc_destroy()
            exists = False
            is_remote_correct = False

        # Checking again, DVC might have been destroyed by this point
        if not exists:
            dvc_init()

        if not is_remote_correct:
            dvc_add_remote(storage_path)
