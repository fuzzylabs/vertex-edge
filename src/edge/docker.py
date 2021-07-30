import subprocess


def build_docker(docker_path, image_name, tag="latest"):
    subprocess.check_output(f"docker build -t {image_name}:{tag} {docker_path}", shell=True)


def push_docker(image_name, tag="latest"):
    subprocess.check_output(f"docker push {image_name}:{tag}", shell=True)
