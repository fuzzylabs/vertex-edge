<p align="center"><img src="./vertex-edge-logo.png" alt="Vertex Edge Logo" height="200"/></a></p>
<p align="center">Connecting the Vertices on GCP</p>
<p align="center">
	<img src="https://img.shields.io/github/repo-size/fuzzylabs/vertex-edge" height="20"/></a>
    <a href="https://circleci.com/gh/fuzzylabs/vertex-edge/tree/master"><img src="https://circleci.com/gh/fuzzylabs/vertex-edge/tree/master.svg?style=svg" alt="CircleCI" height="20"/></a>
</p><br/>

This repository showcases _edge_, a tool for deploying models to [Vertex](https://cloud.google.com/vertex-ai/docs/start) on [Google Cloud Platform](https://cloud.google.com). We've also provided a reference example that shows how to train and deploy a simple model to GCP, and we show how to get up-and-running with everything you need to do MLOps _right_ (in our opinion).

You can use this repo as a template for your projects. To get started, first [**fork this repo**](https://github.com/fuzzylabs/vertex-edge/fork) and then follow the instructions in this README to configure the tools for your GCP enviroment. By the end, you'll have an MLOps-ready environment with a simple model trained and deployed.

## Feedback and contributions

This is a new project and we're keen to get feedback from the community that will help us to improve it. Please do **raise and discuss issues**, send us pull requests, and don't forget to **~~like and subscribe~~** star and fork.

**If you want to contribute** then please check out our [contributions guide](CONTRIBUTING.md), and we'll look forward to contributions!

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

* **[Getting started guide](#getting_started)**
  * Pre-requisites
  * Setting up a GCP environment
  * Authenticating with GCP
  * Initialising vertex:edge
  * Setting up data version control
  * Training a model
  * Deploying your trained model
  * Tracking experiments
* **[Concepts](#concepts)** - a detailed guide to the underlying MLOps concepts used in this example.
* **[Local development guide](#local_dev)**

More documentation

* **[Contributing](CONTRIBUTING.md)**

<a name="getting_started"></a>
# Getting started guide

In this guide, we'll work through the fundamentals of the vertex:edge tool. By the end you'll have trained and deployed a model to GCP.

In order to keep the pre-requisites small, all of the commands run on a Docker container.

## Pre-requisites

* [Docker](https://docs.docker.com/get-docker) (version 18 or greater).
* [gcloud command line tool](https://cloud.google.com/sdk/docs/install).

## Setting up GCP environment

Now you'll need a [GCP account](https://cloud.google.com), so sign up for one if you haven't already done so.

Within your GCP account, [create a new project](https://cloud.google.com/resource-manager/docs/creating-managing-projects), or you can use an existing project if you prefer.

Make sure you [enable billing](https://cloud.google.com/billing/docs/how-to/modify-project) for your new project too.

## Authenticating with GCP

If you haven't got the `gcloud` command line tool, [install it now](https://cloud.google.com/sdk/docs/install).

Then authenticate by running:

```
gcloud auth login
```

Followed by

```
gcloud auth application-default login
```

Next you need to configure the project ID. This should be the project which you created during 'Setting up GCP environment' above.

```
gcloud config set project <your project ID>
```

Finally, you'll need to configure a region. Please see the [GCP documentation](https://cloud.google.com/vertex-ai/docs/general/locations#feature-availability) to understand which regions are available for Vertex.

```
gcloud config set compute/region <region name>
```

## Initialising vertex:edge

Before you can use vertex:edge to train models, you'll need to initialise it (this only needs to be done once).

```
./edge.sh init
```

When you run this for the first time, it will first download a Docker image (`fuzzylabs/edge`).

The initialisation step will first check that your GCP environment is setup correctly and it will confirm your choice of project name and region, so that you don't accidentally install things to the wrong GCP environment.

It will ask you to choose a name for a cloud storage bucket. This bucket is used for tracking the vertex:edge state, for data version control and for model assets. Keep in mind that on GCP, storage bucket names are **globally unique**, so you might find that the name you want to use is already taken (in which case vertex:edge will give you an error message). For more information please see the [official GCP documentation](https://cloud.google.com/storage/docs/naming-buckets).

## Setting up data version control

Before we set up data version control, we need to do one housekeeping step. Because this repository has been set up as a fully-working example, it's already got some DVC configuration files, but these files reference our GCP environment, so you'll need to clear these before setting DVC for your environment:

```
./clear_data.sh
```

With that out of the way, you can go ahead and run you can go ahead and run:

```
./edge.sh dvc init
```

Which does two things:

* Configure DVC locally so that you can version your data.
* Set up remote storage using a Google Cloud Bucket so that versioned data is stored centrally.

At this point, if you're not already familiar with DVC, it may be a good idea to familiarise yourself with this a little before continuing by reading the [DVC official documentation](https://dvc.org/doc). Of course, if you'd prefer to defer that to later, you can carry on to training and deploying the model.

## Training a model

Once you've set up DVC, you're ready to train the example model.

The model that we're going to train is based on the [Fashion MNIST](https://github.com/zalandoresearch/fashion-mnist) dataset. Some important things to remember:

* We don't store the datasets in Git, so before you can train the model, you'll use a script to download the dataset and add it to DVC (data version control).
* All training is done on Vertex. We currently don't support local training, i.e. running the training script on your own computer.

### Seeding the dataset

We'll run these commands inside the Docker container. You can get a Bash shell within the container by running:

```
./edge.sh bash
```

Within this shell you can run:

```
./seed_data.sh
```

Which downloads the fashion dataset, followed by:

```
dvc push
```

To push the newly downloaded data to data version control.

Finally, exit the shell by running `exit`.

### Initialising the model

Before we can train a model, we need to initialise it. This is so that vertex:edge can keep track of the model's lifecycle. To initialise the fashion model, run:

```
./edge.sh model init
```

You'll be asked to provide a name for the model. You can enter anything here, for instance `fashion`.

### Running the training pipeline

Now that the model has been initialised we can run the training pipeline. We've used DVC to manage model pipelines. The pipeline does two things:

1. Generate a training and test dataset using the original data that we downloaded earlier.
2. Run a training job on GCP Vertex.

We'll use the vertex:edge Bash shell once again here. Run:

```
./edge.sh bash
```

And within the Bash shell run

```
dvc repro models/fashion/dvc.yaml
```

Then `dvc repro` runs the pipeline itself. This might take a little while to run, but you'll see periodic status updates as it progresses. You can also view the [job in progress in the Google Cloud Console](https://console.cloud.google.com/vertex-ai/training/custom-jobs).

At the end of training remember to exit the Bash session with `exit`.

## Deploying your trained model

Having trained the model, you should see it listed in the [Google Cloud console under 'models'](https://console.cloud.google.com/vertex-ai/models). However, the model hasn't yet been deployed, so we can't interact with it.

Deployment is done with just one command:

```
./edge.sh model deploy
```

To interact with a model, you need to know its _endpoint_. You can get hold of the endpoint associated with the model by running

```
./edge.sh model get-endpoint
```

## Testing the model with some sample payloads

Now we'll do some inference using the deployed model. The file `test_payload.json` contains three images. The images are stored as numerical arrays, and for each image we expect the model to give us a classification.

The script `test_endpoint.sh` will use `test_payload.json` to test the model. You can run:

```
./test_endpoint.sh
```

You should get back the following response

```
{
  "predictions": [
    9,
    2,
    1
  ],
  "deployedModelId": "6884244611645046784"
}
```

The numbers `9`, `2`, `1` represent the predicted classes for the three images. The model itself just gives us numbers, but these correspond to `Ankle boot`, `Trouser`, `T-shirt/top`.

## Tracking experiments

**TODO** experiment tracking isn't currently supported, but we'll be adding this soon. Please see Github issues for more details.

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

<a name="local_dev"></a>
# Local development guide
