import os.path
from serde import serialize, deserialize
from serde.yaml import to_yaml, from_yaml
from dataclasses import dataclass
from google.cloud import storage

from edge.exception import EdgeException
from edge.storage import get_bucket, StorageBucketState
from edge.config import EdgeConfig
from edge.tui import StepTUI, SubStepTUI
from typing import Type, TypeVar, Optional, Dict
from contextlib import contextmanager


@deserialize
@serialize
@dataclass
class SacredState:
    external_omniboard_string: str


@deserialize
@serialize
@dataclass
class ModelState:
    endpoint_resource_name: str
    deployed_model_resource_name: Optional[str] = None


T = TypeVar("T", bound="EdgeState")


@deserialize
@serialize
@dataclass
class EdgeState:
    models: Optional[Dict[str, ModelState]] = None
    sacred: Optional[SacredState] = None
    storage: Optional[StorageBucketState] = None

    def save(self, _config: EdgeConfig):
        client = storage.Client(project=_config.google_cloud_project.project_id)
        bucket = client.bucket(_config.storage_bucket.bucket_name)
        blob = storage.Blob(".edge_state/edge_state.yaml", bucket)
        blob.upload_from_string(to_yaml(self))


    @classmethod
    def load(cls: Type[T], _config: EdgeConfig) -> T:
        client = storage.Client(project=_config.google_cloud_project.project_id)
        bucket = client.bucket(_config.storage_bucket.bucket_name)
        blob = storage.Blob(".edge_state/edge_state.yaml", bucket)

        if blob.exists():
            return from_yaml(EdgeState, blob.download_as_bytes(client).decode("utf-8"))
        else:
            raise EdgeException(f"State file is not found in '{_config.storage_bucket.bucket_name}' bucket."
                                f"Initialise vertex:edge state by running `./edge.py init.`")

    @classmethod
    @contextmanager
    def context(
            cls: Type[T],
            _config: EdgeConfig,
            to_lock: bool = False,
            to_save: bool = False,
            silent: bool = False
    ) -> T:
        with StepTUI("Loading vertex:edge state", emoji="💾", silent=silent):
            state = None
            locked = False

            if to_lock:
                with SubStepTUI("Locking state", silent=silent):
                    locked = EdgeState.lock(_config.google_cloud_project.project_id,
                                            _config.storage_bucket.bucket_name)

            with SubStepTUI("Loading state", silent=silent):
                state = EdgeState.load(_config)
        try:
            yield state
        finally:
            if (to_save and state is not None) or locked:
                with StepTUI("Saving vertex:edge state", emoji="💾", silent=silent):
                    if to_save and state is not None:
                        with SubStepTUI("Saving state", silent=silent):
                            state.save(_config)
                    if locked:
                        with SubStepTUI("Unlocking state", silent=silent):
                            EdgeState.unlock(_config.google_cloud_project.project_id,
                                             _config.storage_bucket.bucket_name)

    @classmethod
    def exists(cls: Type[T], _config: EdgeConfig) -> bool:
        client = storage.Client(project=_config.google_cloud_project.project_id)
        bucket = client.bucket(_config.storage_bucket.bucket_name)
        blob = storage.Blob(".edge_state/edge_state.yaml", bucket)
        return blob.exists()

    @classmethod
    def lock(cls, project: str, bucket_name: str, blob_name: str = ".edge_state/edge_state.yaml") -> bool:
        """
        Lock the state file in Google Storage Bucket

        :param project:
        :param bucket_name:
        :param blob_name:
        :return: (bool, bool) -- is lock successful, is state to be locked later
        """
        bucket = get_bucket(project, bucket_name)
        if bucket is None or not bucket.exists():
            raise EdgeException("Google Storage Bucket does not exist. Initialise it by running `./edge.py init.`")
        blob = storage.Blob(f"{blob_name}.lock", bucket)
        if blob.exists():
            raise EdgeException("State file is already locked")

        blob.upload_from_string("locked")
        return True

    @classmethod
    def unlock(cls, project: str, bucket_name: str, blob_name: str = ".edge_state/edge_state.yaml"):
        bucket = get_bucket(project, bucket_name)
        blob = storage.Blob(f"{blob_name}.lock", bucket)

        if bucket is not None and blob.exists():
            blob.delete()
