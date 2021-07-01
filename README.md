# Vertex-Edge

In this reference example we demonstrate MLOps on Google Cloud Platform with Vertex. This represents what we at Fuzzy Labs consider to be _MLOps done right_.

## Motivation

At the beginning of this project, we set out to address the following questions:

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

The README has two parts. First, we explain the concepts that underlie the reference example. Second, we explain step-by-step how to setup and run the example in your GCP environment.

* **[Concepts](#concepts)**
* **[How to run the example - step-by-step](#running)**

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
* It allows us to link every experiment to a specific data version.

We use DVC to do data versioning.

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

We use Sacred for experiment tracking.

## Adding cloud training infrastructure (Vertex AI)

While at the start of a project we're usually doing everything locally, on our own computers, we ultimately want the ability to train a model on cloud-based resources. This gives us more computational power, but it also centralises training and prepares us for cloud-based deployment, which will come later.

By this point we've already got a model training pipeline in DVC, but we add an option to run the training itself on Google Vertex. Running it locally is still possible, of course.

<!-- need to explain a little bit more of what the pipeline entails and where the handoff is to GCP. Also, how data is accessed differently in GCP vs local -->

## Training plus deployment: CI/CD

Finally, we want to deploy a model. We introduce CI/CD, using Circle CI, for this. A Circle pipeline itself invokes the model pipeline. The model pipeline in turn starts a training job on Vertex. It also pushes an experiment to experiment tracking, and a trained model to the Vertex model registry.

The model is deployed along with an endpoint, which exposes the model for online inference.

## Monitoring

<!-- TODDO -->

## Project layout
<!--
data/{...}
models/model1

models/pipelines/{p1, p2....}   ->
   every time a pipeline runs, whether locally or on Vertex, an experiment must be logged centrally.
   What is logged? the tasks themselves (input + output), and the lineage
   What goes into a lineage? versioned inputs, outputs, versioned data
   The thing that runs the pipeline builds the lineage

services/...

.circle/pipelines
-->

<a name="running"></a>
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

## Authenticate with GCP

```
gcloud auth login
gcloud auth application-default login
```

<!-- TODO: verify this. Application default login too? -->

<!-- unset GOOGLE_APPLICATION_CREDENTIALS -->

## Edge setup script

[comment]: <> (TODO:)

[comment]: <> (* What resources it sets up)

[comment]: <> (* CircleCI setup)

[comment]: <> (* DVC seeding)

[comment]: <> (* Running pipelines, deploying model and webapp from local machine)

To setup the project with Google Cloud run:
```
python edge.py setup
```

This command will run the configuration wizard to create a config (if `edge.yaml` does not exist), and set up 
Google Cloud resources according to the configuration

To explicitly run configuration wizard and override the config:
```
python edge.py config
```

Seed the data
```
./seed_data.sh 
git add data/fashion-mnist/.gitignore data/fashion-mnist/*.dvc
```

## Provision the dataset Google Cloud storage

When setting this example up for the first time in your GCP environment, you'll need to initialise the dataset.

<!-- TODO: steps -->

## Pull the dataset

```
dvc pull
```

## Train the model locally

First, to get an idea as to what the model training looks like, we can run the training script alone with no bits added.

```
cd step0
python train.py
```

<!-- comment on the model and dataset -->

## Provision the experiment tracker

For experiment tracking, we need an instance of [Sacred](https://github.com/IDSIA/sacred). Sacred works in conjunction with MongoDB, which is used to store the experiments themselves, and [Omniboard](https://vivekratnavel.github.io/omniboard/#/README), which provides the user interface for Sacred.

<!-- TODO: we should encourage people to run this in GCP. Perhaps remove the local instructions -->
Typically you'll want to provision Sacred in GCP, so that you have centralised experiment tracking. You can also run it locally for testing purposes.

### Running experiment tracking in GCP

<!-- TODO -->

### Running experiment tracking locally

We'll use Docker to run Sacred locally. First, start MongoDB:

```
docker run --name mongo -p 27017:27017 -d mongo:latest
```

Next, launch Omniboard, which will provide us with a user interface with which to view experiments:

```
docker run -it --rm -p 9000:9000 --network host --name omniboard vivekratnavel/omniboard -m localhost:27017:sacred
```

You can now open the dashboard in your browser [http://localhost:9000](http://localhost:9000).

## Train the model locally with DVC pipeline

This time, we train the model through a model training pipeline, which uses DVC. We also log the training to our experiment tracker.

```
cp dvc-step1.yaml dvc.yaml
dvc repro
```

This step uses [Sacred](https://github.com/IDSIA/sacred) for experiment tracking. The results are saved to MongoDB.

## Train the model on Vertex AI

This step is the same as before, except that this time we will run the training step on Vertex. The pipeline still executes locally, but the training step will invoke the Vertex API in order to run the training step there.

```
cp dvc-step2.yaml dvc.yaml
dvc repro
```

## Train and deploy on Vertex AI

<!-- TODO -->

```
cp dvc-step2.yaml dvc.yaml
dvc repro
python deploy-vertex.py
```
