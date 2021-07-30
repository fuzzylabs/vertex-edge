from edge.config import EdgeConfig
from edge.exception import EdgeException
from edge.gcloud import is_authenticated, project_exists, is_billing_enabled
from edge.tui import SubStepTUI, StepTUI


def check_gcloud_authenticated():
    with SubStepTUI(message="️Checking if you have authenticated with gcloud") as sub_step:
        _is_authenticated, _reason = is_authenticated()
        if not _is_authenticated:
            raise EdgeException(_reason)


def check_project_exists(gcloud_project: str):
    with SubStepTUI(f"Checking if project '{gcloud_project}' exists") as sub_step:
        project_exists(gcloud_project)


def check_billing_enabled(gcloud_project: str):
    with SubStepTUI(f"Checking if billing is enabled for project '{gcloud_project}'") as sub_step:
        if not is_billing_enabled(gcloud_project):
            raise EdgeException(
                f"Billing is not enabled for project '{gcloud_project}'. "
                f"Please enable billing for this project following these instructions "
                f"https://cloud.google.com/billing/docs/how-to/modify-projectBilling is not enabled "
                f"for project '{gcloud_project}'."
            )


def precommand_checks(config: EdgeConfig):
    gcloud_project = config.google_cloud_project.project_id
    with StepTUI(message="Checking your GCP environment", emoji="☁️") as step:
        check_gcloud_authenticated()
        check_project_exists(gcloud_project)
        check_billing_enabled(gcloud_project)