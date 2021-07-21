import json
import subprocess
from dataclasses import dataclass
from .exception import EdgeException


@dataclass
class Version:
    major: int
    minor: int
    patch: int

    @classmethod
    def from_string(cls, version_string: str):
        version_string = version_string.split("+")[0].strip("v")
        ns = [int(x) for x in version_string.split(".")]
        return Version(*ns)

    def is_at_least(self, other):
        if self.major > other.major:
            return True
        elif self.major == other.major:
            if self.minor > other.minor:
                return True
            elif self.minor == other.minor:
                if self.patch >= other.patch:
                    return True
        return False

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"


def command_exist(command) -> bool:
    try:
        subprocess.check_output(f"which {command}", shell=True, stderr=subprocess.STDOUT)
        return True
    except subprocess.CalledProcessError:
        return False


def get_version(command) -> str:
    try:
        version_string = subprocess.check_output(command, shell=True, stderr=subprocess.DEVNULL).decode("utf-8")
        return version_string
    except subprocess.CalledProcessError:
        raise EdgeException(f"Unexpected error, while trying to get version with `{command}`")


def get_gcloud_version() -> Version:
    if not command_exist("gcloud"):
        raise EdgeException("Unable to locate gcloud. Please visit https://cloud.google.com/sdk/docs/install for installation instructions.")
    version_string = get_version("gcloud version --format json")
    return Version.from_string(json.loads(version_string)["core"])


def get_kubectl_version() -> Version:
    if not command_exist("kubectl"):
        raise EdgeException("Unable to locate kubectl. Please visit https://kubernetes.io/docs/tasks/tools/ for installation instructions.")
    version_string = get_version("kubectl version --client=true --short -o json")
    return Version.from_string(json.loads(version_string)["clientVersion"]["gitVersion"])


def get_helm_version() -> Version:
    if not command_exist("helm"):
        raise EdgeException("Unable to locate helm. Please visit https://helm.sh/docs/intro/install/ for installation instructions.")
    version_string = get_version("helm version --short")
    return Version.from_string(version_string)
