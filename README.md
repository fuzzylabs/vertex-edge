# Vertex-Edge
[![CircleCI](https://circleci.com/gh/fuzzylabs/vertex-edge/tree/master.svg?style=svg)](https://circleci.com/gh/fuzzylabs/vertex-edge/tree/master)

[comment]: <>(add the CirclCI widget)

In this reference example we demonstrate MLOps on Google Cloud Platform using [Vertex](https://cloud.google.com/vertex-ai/docs/start). This represents what we at Fuzzy Labs consider to be _MLOps done right_.

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

The README has three parts:

* First, we explain the concepts that underlie the reference example.
* Next we explain step-by-step how to setup the necessary tools in your GCP environment.
* Finally, we cover how to train and deploy your first model.

...

* **[Concepts](#concepts)**
* **[How to run the example - step-by-step](#installing)**
* **[Training your first model](#running)**
* **[Setting up CI/CD with CircleCI](#circle)**

<a name="concepts"></a>
# Concepts

<!-- perhaps move this paragraph further down -->
Any productionised machine learning project will consist not only of models but other software components that are necessary in order to make those models useful. We will typically be building models along-side other pieces of software. Both of these need to be tracked, deployed, and monitored, but the approach taken for models differs somewhat from other kinds of software.
<!-- -->

A machine learning model passes through a few stages of maturity:

## Experimental phase

We imagine a team of data scientists starting from scratch on a particular problem. Every problem is different but we can still introduce some tools in this phase that will make life easier.

### The data

<!-- what about VC on unstructured data? -->
The data may not be well-understood, and it may be incomplete. It's important to have data version control from the very start, because:

* It's easier for a team to share data while ensuring that everybody is working with the same version of that data.
* It allows us to track changes over time.
* It allows us to link every experiment and deployed model to a specific data version.

We use [DVC](https://dvc.org) to do data versioning.

### The code

As we're going to be training a model, we're going to need to write some code as well. Code versioning is just as important as data versioning, for exactly the same reasons as stated above.

We're using Git to track code versions. Additionally, it's worth noting that DVC interoperates with Git, so this single code repository is enough to get somebody up-and-running with everything they will need in order to train the model.

Training a model involves a few steps. At the very least, we must prepare data and then run a training script. We use DVC to specify a training pipeline. Something to keep in mind: we're going to be talking about two different kinds of pipeline: as well as the model training pipeline, there will be a deployment pipeline, which we'll come to soon.

### The experiments

Every run of the model pipeline gets logged to a central location. Specifically, we record:

* When it ran, who ran it, and where it ran.
* The Git commit associated with the experiment.
* The data version associated with the experiment.
* The hyperparameters in use.
* The performance of the model.

This way, anybody on the team is able to review past experiments and reproduce them consistently.

We use [Sacred](https://github.com/IDSIA/sacred) with [Omniboard](https://github.com/vivekratnavel/omniboard) for experiment tracking.

## Adding cloud training infrastructure (Vertex AI)

While at the start of a project we're usually doing everything locally, on our own computers, we ultimately want the ability to train a model on cloud-based resources. This gives us more computational power, but it also centralises training and prepares us for cloud-based deployment, which will come later.

By this point we've already got a model training pipeline in DVC, but we add an option to run the training itself on Google Vertex. Running it locally is still possible, of course.
<!-- need to explain a little bit more of what the pipeline entails and where the handoff is to GCP. Also, how data is accessed differently in GCP vs local -->
## Cloud deployment infrastructure (Vertex AI)


<!-- todo -->

## Monitoring

<!-- todo: we want it, we haven't done it, and why -->

## Training plus deployment: CI/CD

Finally, we want to deploy a model. We introduce CI/CD, using Circle CI, for this. A Circle pipeline itself invokes the model pipeline. The model pipeline in turn starts a training job on Vertex. It also pushes an experiment to experiment tracking, and a trained model to the Vertex model registry.

The model is deployed along with an endpoint, which exposes the model for online inference.

## Project layout
<!--TODO: explain current layout-->

## Edge setup script

<!-- TODO: review / update -->

The Vertex:Edge setup script (`edge.py`) is written to simplify setting up a machine learning project
on Google Cloud Platform from scratch

It can:
* Run a configuration wizard and save the resulting config for future use (`edge.yaml`)
* Set up all the necessary resources in GCP, namely
    * Initialise DVC in the repository (if not initialised)
    * Enable required Google Cloud APIs
    * Create a Storage bucket for dataset and model storage
    * Set up Vertex AI Endpoint for model deployment
    * Create Kubernetes cluster and set up Sacred/Omniboard on it for experiment tracking
* Build and push Docker images for a web app, and for model serving
* Deploy a web app to Cloud Run
* Deploy a trained model to Vertex AI

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

<a name="installing"></a>
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
./edge.py docker-vertex-prediction
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
./edge.py vertex-deploy
```

## Web app locally
### Run locally in docker
```
./edge.py run-webapp
```

### Deploy to Cloud Run
```
./edge.py docker-webapp
./edge.py cloud-run-webapp
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
