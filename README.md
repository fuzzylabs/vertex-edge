<p align="center"><img src="./vertex-edge-logo.png" alt="Vertex Edge Logo" height="180"/></a></p>
<p align="center">
	<img src="https://img.shields.io/github/repo-size/fuzzylabs/vertex-edge" height="20"/></a>
    <!--<a href="https://circleci.com/gh/fuzzylabs/vertex-edge/tree/master"><img src="https://circleci.com/gh/fuzzylabs/vertex-edge/tree/master.svg?style=svg" alt="CircleCI" height="20"/></a>-->
</p><br/>

# Vertex:Edge

Adopting MLOps into a data science workflow requires specialist knowledge of cloud engineering. As a data scientist, you just want to train your models and get on with your life. **vertex:edge** provides an environment for training and deploying models on Google Cloud that leverages the best available open-source MLOps to track your experiments and version your data.

<p align="center">
    <img src="demo.gif"/>
</p>

There are two parts to **vertex:edge**:

* A command line tool that can be used to set up your MLOps infrastructure in Google Cloud.
* A Python library that can be used in your model training scripts to help you train those models on Google Vertex.

## Contents

* **[Why vertex:edge](#why-vertex:edge?)**?
* Pre-requisites
* Quick-start
* Tutorials
* Contributing

# Why vertex:edge?



# Pre-requisites

* [A Google Cloud account](https://cloud.google.com).
* [gcloud command line tool](https://cloud.google.com/sdk/docs/install).
* [Docker](https://docs.docker.com/get-docker) (version 18 or greater).
* Python, at least version 3.8.
* PIP, at least version 21.2.0.

It's important to make sure you have an up-to-date PIP version. If you're unsure, run `pip install --upgrade-pip` to upgrade.

# Quick-start

Install vertex:edge using:

```
pip install vertex-edge
```

Initialise your environment and create an empty model:

```
edge init
edge model init hello-world
edge model template hello-world
```

Train the model locally:

```
python models/hello-world/train.py
```

Train it on Google Vertex:

```
RUN_ON_VERTEX=True python models/hello-world/train.py
```

# Tutorials

* [Project setup](tutorials/setup.md)
* [Training and deploying a model to GCP](tutorials/train_deploy.md)
* [Tracking your experiments](tutorials/experiment_tracking.md)

# Contributing

This is a new project and we're keen to get feedback from the community to help us improve it. Please do **raise and discuss issues**, send us pull requests, and don't forget to **~~like and subscribe~~** star and fork this repo.

**If you want to contribute** then please check out our [contributions guide](CONTRIBUTING.md) and [developers guide](DEVELOPERS.md). We look forward to your contributions!
