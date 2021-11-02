<p align="center"><img src="./vertex-edge-logo.png" alt="Vertex Edge Logo" height="180"/></a></p>
<p align="center">
	<img src="https://img.shields.io/github/repo-size/fuzzylabs/vertex-edge" height="20"/></a>
    <!--<a href="https://circleci.com/gh/fuzzylabs/vertex-edge/tree/master"><img src="https://circleci.com/gh/fuzzylabs/vertex-edge/tree/master.svg?style=svg" alt="CircleCI" height="20"/></a>-->
</p><br/>

# Vertex:Edge

Adopting MLOps into a data science workflow requires specialist knowledge of cloud engineering. As a data scientist, you just want to train your models and get on with your life. **vertex:edge** provides an environment for training and deploying models on Google Cloud that leverages the best available open-source MLOps tools to track your experiments and version your data.

<p align="center">
    <img src="demo.gif"/>
</p>

## Contents

* **[Why vertex:edge?](#why-vertexedge)**
* **[Pre-requisites](#pre-requisites)**
* **[Quick-start](#quick-start)**
* **[Tutorials](#tutorials)**
* **[Contributing](#contributing)**

# Why vertex:edge?

**vertex:edge** is a tool that sits on top of Vertex (Google's cloud AI platform). Ordinarily, training and deploying models with Vertex requires a fair amount of repetitive work, and moreover the tooling provided by Vertex for things like data versioning and experiment tracking [aren't quite up-to-scratch](https://fuzzylabs.ai/blog/vertex-ai-the-hype).

**vertex:edge** addresses a number of challenges:

* Training and deploying a model on Vertex with minimal effort.
* Setting up useful MLOps tools such as experiment trackers in Google Cloud, without needing a lot of cloud engineering knowledge.
* Seamlessly integrating MLOps tools into machine learning workflows.

Our vision is to provide a complete environment for training models with MLOps capabilities built-in. Right now we support model training and deployment through Vertex and TensorFlow, experiment tracking thanks to [Sacred](https://github.com/IDSIA/sacred), and data versioning through [DVC](https://dvc.org). In the future we want to not only expand these features, but also add:

* Support for multiple ML frameworks.
* Integration into model monitoring solutions.
* Easy integration into infrastructure-as-code tools such as Terraform.

# Pre-requisites

* [A Google Cloud account](https://cloud.google.com).
* [gcloud command line tool](https://cloud.google.com/sdk/docs/install).
* [Docker](https://docs.docker.com/get-docker) (version 18 or greater).
* Python, at least version 3.8. Check this using `python --version`.
* PIP, at least version 21.2.0. Check this using `pip --version`. To upgrade PIP, run `pip install --upgrade-pip`.

# Quick-start

This guide gives you a quick overview of using **vertex:edge** to train and deploy a model. If this is your first time training a model on Vertex, we recommend reading the more detailed tutorials on [Project Setup](tutorials/setup.md) and [Training and Deploying a Model to GCP](tutorials/train_deploy.md).

## Install vertex:edge

```
pip install vertex-edge
```

## Authenticate with GCP

```
gcloud auth login
gcloud config set project <your project ID>
gcloud config set compute/region <region name>
gcloud auth application-default login
```

## Initialise your project

```
edge init
edge model init hello-world
edge model template hello-world
```

n.b. when you run `edge init`, you will be prompted for a cloud storage bucket name. This bucket is used for tracking your project state, storing trained models, and storing versioned data. Remember that bucket names need to be globally-unique on GCP.

## Train and deploy

After running the above, you'll have a new Python script under `models/hello-world/train.py`. This script uses TensorFlow to train a simple model.

To train the model on Google Vertex, run:

```
RUN_ON_VERTEX=True python models/hello-world/train.py
```

Once this has finished, you can deploy the model using:

```
edge model deploy hello-world
```

You can also train the model locally, without modifying any of the code:

```
pip install tensorflow
python models/hello-world/train.py
```

Note that we needed to install TensorFlow first. This is by design, because we don't want the **vertex:edge** tool to depend on specific ML frameworks.

## Track experiments

We can add experiment tracking with just one command:

```
edge experiments init
```

With experiment tracking enabled, every time you train a model, the details of the training run will be recorded, including performance metrics and training parameters.

You can view all of these experiments in a dashboard. To get the dashboard URL, run:

```
edge experiments get-dashboard
```

<p align="center">
    <img src="omniboard-screenshot.png"/>
</p>

To learn more, read our tutorial on [Tracking your experiments](tutorials/experiment_tracking.md).

## Version data

By using data version control you can always track the history of your data. Combined with experiment tracking, it means each model can be tied to precisely the dataset that was used when the model was trained.

We use [DVC](https://dvc.org) for data versioning. To enable it, run:

```
edge dvc init
```

n.b. you need to be working in an existing Git repository before you can enable data versioning.

To learn more, read our tutorial on [Versioning your data](tutorials/versioning_data.md).

# Tutorials

* [Project Setup](tutorials/setup.md)
* [Training and Deploying a Model to GCP](tutorials/train_deploy.md)
* [Tracking your experiments](tutorials/experiment_tracking.md)
* [Versioning your data](tutorials/versioning_data.md)

# Contributing

This is a new project and we're keen to get feedback from the community to help us improve it. Please do **raise and discuss issues**, send us pull requests, and don't forget to **~~like and subscribe~~** star and fork this repo.

**If you want to contribute** then please check out our [contributions guide](CONTRIBUTING.md) and [developers guide](DEVELOPERS.md). We look forward to your contributions!
