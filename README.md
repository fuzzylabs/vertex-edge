# Vertex:edge

[![CircleCI](https://circleci.com/gh/fuzzylabs/vertex-edge/tree/master.svg?style=svg)](https://circleci.com/gh/fuzzylabs/vertex-edge/tree/master)

This repository showcases _edge_, a tool for deploying models to [Vertex](https://cloud.google.com/vertex-ai/docs/start) on [Google Cloud Platform](https://cloud.google.com). We've also provided a reference example that shows how to train and deploy a simple model to GCP, and we show how to get up-and-running with everything you need to do MLOps _right_ (in our opinion).

## Motivation

With this project we set out to address the following questions:

<!-- TODO: answers -->

* How do we version data?
* How would two data scientists work collaboratively on a model?
* How do we track experiments?
* How do we set up a training pipeline in the cloud?
* How do we test the model?
* How do we serve the model?
* How do other software components interact with the model?
* How do we monitor the model the model on an ongoing basis?

## Table of Contents

* **[Concepts](#concepts)** - the underlying MLOps concepts in this example.
* **[Installing on your GCP environment](#installing)**
* **[Training your first model in GCP](#running)**
* **[Setting up CI/CD with CircleCI](#circle)**

<a name="concepts"></a>
# Concepts

Any productionised machine learning project will consist not only of models but other software components that are necessary in order to make those models useful. We will typically be building models along-side other pieces of software. Both of these need to be tracked, deployed, and monitored, but the approach taken for models differs somewhat from other kinds of software.

A machine learning model passes through a few stages of life. Let's look at those stages.

## Experimental phase

Imagine a team of data scientists starting a project from scratch. At this stage there are numerous unknowns, but we can still introduce some tools that will make life easier.

### The data

The data may not be well-understood, and it may be incomplete. It's important to have data version control from the very start, because:

* It's easier for a team to share data while ensuring that everybody is working with the same version of that data.
* It allows us to track changes over time.
* We can link every experiment and deployed model to a specific data version.

We use [DVC](https://dvc.org) to do data versioning. DVC has a number of other features, including pipelines, which we'll discuss next.

### The code

Ultimately we want to train a model, so we'll need to write some code as well. Code versioning is just as important as data versioning, for exactly the same reasons as stated above.

We're using Git to track code versions. It's worth noting that DVC interoperates with Git, so this single code repository is enough to get somebody up-and-running with everything they will need in order to train the model.

Training a model involves a few steps. At the very least, we must prepare data and then run a training script. We use DVC to specify a training pipeline. Something to keep in mind: we're going to be talking about two different kinds of pipeline:

* **Model training pipeline** - a DVC pipeline which first prepares the training data, and then trains a model.
* **CI / CD pipeline** - using [CircleCI](https://circleci.com) we can combine training and deployment into a single pipeline.

This admittedly gets a little bit confusing, because 'pipeline' means two different things depending on the context. The CI/CD pipeline itself runs the model training pipeline.

### Experiments

Every run of the model training pipeline gets logged to a central location. Any time we run this pipeline, we call that an experiment. In any experiment, we record:

* When it ran, who ran it, and where it ran.
* The Git commit associated with the experiment.
* The data version associated with the experiment.
* The hyperparameters in use.
* The performance of the model.

This way, anybody on the team is able to review past experiments and reproduce them consistently.

We use [Sacred](https://github.com/IDSIA/sacred) with [Omniboard](https://github.com/vivekratnavel/omniboard) for experiment tracking (MongoDB is used as the backing database). The _vertex:edge_ tool will install the experiment tracker into your GCP environment so that you can log and review experiments.

## Adding cloud training infrastructure (Vertex AI)

When it comes to training our model, we want to use cloud-based resources. This gives us more computational power, but it also centralises training and prepares us for cloud-based deployment, which will come later.

Vertex can already train models in the cloud - that's what it does best! - but we also want it to work seamlessly with data versioning and experiment tracking.

The DVC model training pipeline has two steps:

* Data preparation: generate a training and testing dataset.
* Train: execute a training script on Vertex and capture the resulting model.

## Cloud deployment infrastructure (Vertex AI)

<!-- todo -->

## Monitoring

Once a model has been deployed, we'd ideally like to monitor it. The purpose of monitoring a model is to make us aware of changes to its behaviour. Changes come for example through shifts in the input data. Additionally, we want to know about potential biases in the training data.

In response to monitoring we can make informed decisions. For instance we might decide to re-train the model with new data if we feel that this model no longer reflects reality in some way.

We haven't implemented any monitoring so far in this project, but this is something we'd like to add in the future.

## Training plus deployment: CI/CD

Finally, we want to deploy a model. We introduce CI/CD, using Circle CI, for this. A Circle pipeline itself invokes the model pipeline. The model pipeline in turn starts a training job on Vertex. It also pushes an experiment to experiment tracking, and a trained model to the Vertex model registry.

The model is deployed along with an endpoint, which exposes the model for online inference.

## Project layout

Here's a brief guide to how this project is organised:

* [data](data) - data used for our example model. This data comes from the [Fashion MNIST](https://github.com/zalandoresearch/fashion-mnist) dataset. We _don't commit the data_ to Git; DVC manages the data.
* [edge](edge) - code for the vertex:edge tool.
* [models](models) - each model has its own sub-directory under `models`, and within each model directory we have training code and the training pipeline.
* [services](services) - models by themselves aren't useful without things that interact with the model. `services` contains deployable web services that interact with models.

## Edge setup script

Finally, we come to the vertex:edge tool (`edge.py`) whose purpose is to simplify setting up a machine learning project on Google Cloud Platform from scratch.

It can:

* Run a configuration wizard and save the resulting config for future use.
* Set up all the necessary resources in GCP, namely
    * Initialise DVC in the repository.
    * Enable required Google Cloud APIs.
    * Create a Storage bucket for dataset and model storage.
    * Set up Vertex AI Endpoint for model deployment.
    * Create Kubernetes cluster and set up Sacred / Omniboard on it for experiment tracking.
* Build and push Docker images for a web app, and for model serving.
* Deploy a web app to Cloud Run.
* Deploy a trained model to Vertex AI.

Next we'll look at how to use this script to setup an MLOps-ready project in GCP.

<a name="installing"></a>
# How to run the example - step-by-step

## Prerequisites 
* Python 3
* gcloud
* helm
* kubectl

## Setup Python environment

To make collaboration go smoothly, we really want to make sure that every developer can reproduce the same development environment, which means everybody uses the same versions of Python, and the same Python dependencies.

### PyEnv

First, to manage Python, we'll use [PyEnv](https://github.com/pyenv/pyenv). Follow the instructions for your operating system; once installed, PyEnv will download and make available the appropriate version of Python for you.

The Python version for this project is kept in [.python-version](.python-version). We can install and activate this version of Python by running:

```
pyenv local
```

After this, run `python --version` and ensure that it matches the version states in [.python-version](.python-version).

### Dependencies (venv + PIP)

With the correct version of Python set up, we'll use [Python venv](https://docs.python.org/3/library/venv.html) to provide an isolated Python environment, and [PIP](https://pypi.org/project/pip) to install and manage Python dependencies.

```
python -m venv env/
source env/bin/activate
pip install -r requirements.txt
```

[comment]: <> (add pip version)

## Setting up GCP environment

<!-- TODO -->

* Pre-requisite: a GCP account, link to sign up
* Next create a project and note down project ID

## Authenticate with GCP

```
gcloud auth login
gcloud auth application-default login
```

<!-- TODO: explain specifics of GCloud authentication -->

## Run the configuration script

<!-- TODO: configure for your GCP environment -->

...

```
./edge.py config
```

## Install on GCP

To setup the project with Google Cloud run:

```
./edge.py install
```

## Uninstall from GCP

If you need to uninstall...

```
./edge.py uninstall
```

<a name="running"></a>
# Training your first model

<!-- todo: general explanation of what we'll train, what dataset we'll use. Mention that we're not running the training locally, it's not designed to work this way -->

## Dataset seeding

When you set up this project with a forked git repo, DVC will not have the dataset in Google Storage.
To download [Fashion-MNIST](https://github.com/zalandoresearch/fashion-mnist) dataset and add it to DVC run the following commands:

```
./seed_data.sh 
```

Follow DVC instructions, GIT commit

```
dvc push
```

<!-- link to DVC docs here for remote storage management -->

[comment]: <> (* CircleCI setup)

[comment]: <> (* Running pipelines, deploying model and webapp from local machine)

## Running the training pipeline

### Pull the dataset

<!-- when running for the first time, this won't do anything, but in general practice we should pull the data before running -->

```
dvc pull
```

### Build and push model serving Docker image

<!-- only need to do this if the model serving code has changed -->

```
./edge.py vertex build-docker
```

### Run training pipeline

```
dvc repro models/fashion/dvc.yaml
```

<!-- TODO: add docs link for DVC pipelines -->

## Viewing experiments with the experiment tracker

To get the URL of the experiment tracker dashboard:

```
./edge.py omniboard
```

<!-- TODO: explain -->

## Deploy trained model
```
./edge.py vertex deploy
```

## Web app locally
### Run locally in docker
```
./edge.py webapp run
```

### Deploy to Cloud Run
```
./edge.py webapp build-docker
./edge.py webapp deploy
```

<a name="circle"></a>
# CircleCI setup
## Activate project in CircleCI
Follow [the instructions](https://circleci.com/docs/2.0/getting-started/?section=getting-started#setting-up-circleci)
## Add Google Cloud service account 
Follow [the instructions](https://circleci.com/docs/2.0/google-auth/#creating-and-storing-a-service-account)

Roles that the service account must have:
* Vertex AI user
* Service Account User
* Cloud Run Admin
* Secret Manager Secret Accessor
* Storage Admin
* GKE admin
