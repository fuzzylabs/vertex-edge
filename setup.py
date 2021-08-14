#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="vertex:edge",
    version="0.1.1",
    url="https://github.com/fuzzylabs/vertex-edge",
    package_dir={'': 'src'},
    packages=find_packages("src/"),
    scripts=["edge", "src/vertex_edge.py"],
    include_package_data=True,
    install_requires=[
        "pyserde==0.4.0",
        "google-api-core==1.17.0",
        "grpcio==1.27.0",
        "google-cloud-container==2.4.1",
        "google-cloud-secret-manager==2.5.0",
        "google_cloud_aiplatform==1.1.1",
        "google-cloud-storage==1.38.0",
        "cookiecutter==1.7.3",
        "dvc[gs]==2.5.0",
        "sacred==0.8.2",
        "pymongo==3.11.4",
        "questionary==1.10.0",
        "joblib==1.0.1"
    ]
)
