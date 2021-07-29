from edge.command.common.precommand_check import check_gcloud_authenticated, check_project_exists, check_billing_enabled
from edge.config import GCProjectConfig, StorageBucketConfig, EdgeConfig
from edge.enable_api import enable_service_api
from edge.exception import EdgeException
from edge.gcloud import is_authenticated, get_gcloud_account, get_gcloud_project, get_gcloud_region, get_gcp_regions, \
    project_exists, is_billing_enabled
from edge.state import EdgeState
from edge.storage import setup_storage
from edge.tui import TUI, StepTUI, SubStepTUI, TUIStatus, qmark
from edge.versions import get_gcloud_version, Version, get_kubectl_version, get_helm_version
from edge.path import get_model_dvc_pipeline
import questionary


def edge_init():
    success_title = "Initialised successfully"
    success_message = f"""
What's next? We suggest you proceed with:

  Commit the new vertex:edge configuration to git:
    git add edge.yaml && git commit -m "Initialise vertex:edge"

  Configure an experiment tracker (optional):
    ./edge.sh experiments init

  Configure data version control:
    ./edge.sh dvc init

  Train and deploy a model (see 'Training a model' section of the README for more details):
    ./edge.sh model init fashion
    dvc repro {get_model_dvc_pipeline("fashion")}
    ./edge.sh model deploy fashion

Happy herding! 🐏
        """.strip()
    failure_title = "Initialisation failed"
    failure_message = "See the errors above. See README for more details."
    with TUI(
            "Initialising vertex:edge",
            success_title,
            success_message,
            failure_title,
            failure_message
    ) as tui:
        with StepTUI(message="Checking your local environment", emoji="🖥️") as step:
            with SubStepTUI("Checking gcloud version") as sub_step:
                gcloud_version = get_gcloud_version()
                expected_gcloud_version_string = "2021.05.21"
                expected_gcloud_version = Version.from_string(expected_gcloud_version_string)
                if not gcloud_version.is_at_least(expected_gcloud_version):
                    raise EdgeException(
                        f"We found gcloud version {str(gcloud_version)}, "
                        f"but we require at least {str(expected_gcloud_version)}. "
                        "Update gcloud by running `gcloud components update`."
                    )

                try:
                    gcloud_alpha_version = get_gcloud_version("alpha")
                    expected_gcloud_alpha_version_string = "2021.07.19"
                    expected_gcloud_alpha_version = Version.from_string(expected_gcloud_alpha_version_string)
                    if not gcloud_alpha_version.is_at_least(expected_gcloud_alpha_version):
                        raise EdgeException(
                            f"We found gcloud alpha component version {str(gcloud_alpha_version)}, "
                            f"but we require at least {str(expected_gcloud_alpha_version)}. "
                            "Update gcloud by running `gcloud components update`."
                        )
                except KeyError:
                    raise EdgeException(
                        f"We couldn't find the gcloud alpha components, "
                        f"please install these by running `gcloud components install alpha`"
                    )

            with SubStepTUI("Checking kubectl version") as sub_step:
                kubectl_version = get_kubectl_version()
                expected_kubectl_version_string = "v1.19.0"
                expected_kubectl_version = Version.from_string(expected_kubectl_version_string)
                if not kubectl_version.is_at_least(expected_kubectl_version):
                    raise EdgeException(
                        f"We found gcloud version {str(kubectl_version)}, "
                        f"but we require at least {str(expected_kubectl_version)}. "
                        "Please visit https://kubernetes.io/docs/tasks/tools/ for installation instructions."
                    )

            with SubStepTUI("Checking helm version") as sub_step:
                helm_version = get_helm_version()
                expected_helm_version_string = "v3.5.2"
                expected_helm_version = Version.from_string(expected_helm_version_string)
                if not helm_version.is_at_least(expected_helm_version):
                    raise EdgeException(
                        f"We found gcloud version {str(helm_version)}, "
                        f"but we require at least {str(expected_helm_version)}. "
                        "Please visit https://helm.sh/docs/intro/install/ for installation instructions."
                    )

        with StepTUI(message="Checking your GCP environment", emoji="☁️") as step:
            check_gcloud_authenticated()

            with SubStepTUI(message="Verifying GCloud configuration") as sub_step:
                gcloud_account = get_gcloud_account()
                if gcloud_account is None or gcloud_account == "":
                    raise EdgeException(
                        "gcloud account is unset. "
                        "Run `gcloud auth login && gcloud auth application-default login` to authenticate "
                        "with the correct account"
                    )

                gcloud_project = get_gcloud_project()
                if gcloud_project is None or gcloud_project == "":
                    raise EdgeException(
                        "gcloud project id is unset. "
                        "Run `gcloud config set project $PROJECT_ID` to set the correct project id"
                    )

                gcloud_region = get_gcloud_region()
                if gcloud_region is None or gcloud_region == "":
                    raise EdgeException(
                        "gcloud region is unset. "
                        "Run `gcloud config set compute/region $REGION` to set the correct region"
                    )

                sub_step.update(status=TUIStatus.NEUTRAL)
                sub_step.set_dirty()

                if not questionary.confirm(f"Is this the correct GCloud account: {gcloud_account}", qmark=qmark).ask():
                    raise EdgeException(
                        "Run `gcloud auth login && gcloud auth application-default login` to authenticate "
                        "with the correct account"
                    )
                if not questionary.confirm(f"Is this the correct project id: {gcloud_project}", qmark=qmark).ask():
                    raise EdgeException("Run `gcloud config set project <project_id>` to set the correct project id")
                if not questionary.confirm(f"Is this the correct region: {gcloud_region}", qmark=qmark).ask():
                    raise EdgeException("Run `gcloud config set compute/region <region>` to set the correct region")

            with SubStepTUI(f"{gcloud_region} is available on Vertex AI") as sub_step:
                if gcloud_region not in get_gcp_regions(gcloud_project):
                    formatted_regions = "\n      ".join(get_gcp_regions(gcloud_project))
                    raise EdgeException(
                        "Vertex AI only works in certain regions. "
                        "Please choose one of the following by running `gcloud config set compute/region <region>`:\n"
                        f"      {formatted_regions}"
                    )

            gcloud_config = GCProjectConfig(
                project_id=gcloud_project,
                region=gcloud_region,
            )

            check_project_exists(gcloud_project)
            check_billing_enabled(gcloud_project)

        with StepTUI(message="Initialising Google Storage and vertex:edge state file", emoji="💾") as step:
            with SubStepTUI("Enabling Storage API") as sub_step:
                enable_service_api("storage-component.googleapis.com", gcloud_project)

            with SubStepTUI("Configuring Google Storage bucket", status=TUIStatus.NEUTRAL) as sub_step:
                sub_step.set_dirty()
                storage_bucket_name = questionary.text(
                    "Now you need to choose a name for a storage bucket that will be used for data version control, "
                    "model assets and keeping track of the vertex:edge state\n      "
                    "NOTE: Storage bucket names must be unique and follow certain conventions. "
                    "Please see the following guidelines for more information "
                    "https://cloud.google.com/storage/docs/naming-buckets."
                    "\n      Enter Storage bucket name to use: ",
                    qmark=qmark
                ).ask().strip()
                if storage_bucket_name is None or storage_bucket_name == "":
                    raise EdgeException("Storage bucket name is required")

            storage_config = StorageBucketConfig(
                bucket_name=storage_bucket_name,
                dvc_store_directory="dvcstore",
                vertex_jobs_directory="vertex",
            )
            storage_state = setup_storage(gcloud_project, gcloud_region, storage_bucket_name)

            _state = EdgeState(
                storage=storage_state
            )

            _config = EdgeConfig(
                google_cloud_project=gcloud_config,
                storage_bucket=storage_config,
            )

            skip_saving_state = False
            with SubStepTUI("Checking if vertex:edge state file exists") as sub_step:
                if EdgeState.exists(_config):
                    sub_step.update(
                        "The state file already exists. "
                        "This means that vertex:edge has already been initialised using this storage bucket.",
                        status=TUIStatus.WARNING
                    )
                    sub_step.set_dirty()
                    if not questionary.confirm(
                            f"Do you want to delete the state and start over (this action is destructive!)",
                            qmark=qmark,
                            default=False,
                    ).ask():
                        skip_saving_state = True

            if skip_saving_state:
                with SubStepTUI("Saving state file skipped", status=TUIStatus.WARNING) as sub_step:
                    pass
            else:
                with SubStepTUI("Saving state file") as sub_step:
                    _state.save(_config)

        with StepTUI(message="Saving configuration", emoji="⚙️") as step:
            with SubStepTUI("Saving configuration to edge.yaml") as sub_step:
                _config.save("./edge.yaml")
