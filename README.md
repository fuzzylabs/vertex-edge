<p align="center"><img src="./vertex-edge-logo.png" alt="Vertex Edge Logo" height="200"/></a></p>
<p align="center">
	<img src="https://img.shields.io/github/repo-size/fuzzylabs/vertex-edge" height="20"/></a>
    <!--<a href="https://circleci.com/gh/fuzzylabs/vertex-edge/tree/master"><img src="https://circleci.com/gh/fuzzylabs/vertex-edge/tree/master.svg?style=svg" alt="CircleCI" height="20"/></a>-->
</p><br/>

# Connecting the Vertices on GCP

Adopting MLOps into a data science workflow requires specialist knowledge of cloud engineering. As a data scientist, you just want to train your models and get on with your life. **vertex:edge** helps data scientists adopt MLOps into their workflows. It can set up tools like experiment tracking and data versioning for you, and moreover it helps you to create MLOps-enabled training pipelines, that run seamlessly in [Google Vertex](https://cloud.google.com/vertex-ai/docs/start) as well as locally.

* **Seamless** training in the cloud and locally.
* **Easily adapt** your existing models to train on Vertex.
* **Plugs in to** experiment tracking and data version control.
* **Plays nicely with** CI/CD and infrastructure-as-code frameworks.

In this repository you will find:

* Source code and documentation for the tool itself.
* A step-by-step guide to training and deploying a model to Vertex using **edge**

We've also provided a number of example models in a separate repository, see [Vertex Edge Examples](https://github.com/fuzzylabs/vertex-edge-examples).

## Table of Contents

* **[Getting started](#getting-started)** - a step-by-step guide to training and deploying a model to Vertex using vertex:edge.
  * **[Pre-requisites](#pre-requisites)**
  * **[Preparation](#preparation)**
  * **[Setting up GCP environment](#setting-up-gcp-environment)**
  * **[Authenticating with GCP](#authenticating-with-gcp)**
  * **[Building a simple model](#building-a-simple-model)**

Further documentation

* **[Contributing](CONTRIBUTING.md)** - how to contribute to vertex:edge.
* **[Guide for developers](DEVELOPERS.md)** - some technical guidance for developers who wish to contribute to vertex:edge.
* **[Ready-made examples](https://github.com/fuzzylabs/vertex-edge-examples)**.

## Feedback and contributions

This is a new project and we're keen to get feedback from the community to help us improve it. Please do **raise and discuss issues**, send us pull requests, and don't forget to **~~like and subscribe~~** star and fork this repo.

**If you want to contribute** then please check out our [contributions guide](CONTRIBUTING.md). We look forward to your contributions!

<a name="getting_started"></a>
# Getting started

By the end of this guide you'll have trained and deployed a model to GCP.

## Pre-requisites

* [Docker](https://docs.docker.com/get-docker) (version 18 or greater).
* [gcloud command line tool](https://cloud.google.com/sdk/docs/install).
* Python, at least version 3.8.
* PIP, at least version 21.2.0. It's a good idea to run `pip install --upgrade-pip` to ensure that you have the most recent version.

## Preparation

The very first thing you'll need is a fresh directory in which to work. For instance:

```
mkdir hello-world-vertex
cd hello-world-vertex
```

## Setting up GCP environment

Now you'll need a [GCP account](https://cloud.google.com), so sign up for one if you haven't already done so.

Then within your GCP account, [create a new project](https://cloud.google.com/resource-manager/docs/creating-managing-projects). Take a note of the project ID; you'll be able to view this in the Google Cloud console with the project selection dialog). The project ID won't necessarily match the name that you chose for the project.

Finally make sure you [enable billing](https://cloud.google.com/billing/docs/how-to/modify-project) for your new project too.

## Authenticating with GCP

If you haven't got the `gcloud` command line tool, [install it now](https://cloud.google.com/sdk/docs/install).

Then authenticate by running:

```
gcloud auth login
```

Next you need to configure the project ID. This should be the project which you created during 'Setting up GCP environment' above.

```
gcloud config set project <your project ID>
```

You'll also need to configure a region. Please see the [GCP documentation](https://cloud.google.com/vertex-ai/docs/general/locations#feature-availability) to learn which regions are available for Vertex.

```
gcloud config set compute/region <region name>
```

**Note** `gcloud` might ask you if you want to enable the Google Compute API on the project. If so, type `y` to enable this.

Finally, you need to run one more command to complete authentication:

```
gcloud auth application-default login
```

## Training a model

### Installing vertex:edge

We'll use PIP to install _Edge_:

```
pip install vertex-edge
```

After doing that, you should have the `edge` command available. Try running:

```
edge --help
```

**Note** that when you run `edge` for the first time, it will download a Docker image (`fuzzylabs/edge`), which might take some time to complete. All Edge commands run inside Docker.

### Initialising vertex:edge

Before you can use vertex:edge to train models, you'll need to initialise it (this only needs to be done once).

```
edge init
```

The initialisation step will first check that your GCP environment is setup correctly and it will confirm your choice of project name and region, so that you don't accidentally install things to the wrong GCP environment.

It will ask you to choose a name for a cloud storage bucket. This bucket is used for tracking the vertex:edge state, for data version control and for model assets. Keep in mind that on GCP, storage bucket names are **globally unique**, so you might find that the name you want to use is already taken (in which case vertex:edge will give you an error message). For more information please see the [official GCP documentation](https://cloud.google.com/storage/docs/naming-buckets).

You might wonder what initialisation actually _does_. It sets up two things:

* Creates a configuration file in your project directory, called `edge.yaml`. The configuration includes details about your GCP environment, the models that you have registered, and the cloud storage bucket.
* Creates a _state file_. The state file lives in the cloud storage bucket, and its purpose is to make sure that only one person can modify the GCP environment at any one time.

### Building a simple model

#### Initialisation

First let's initialise a new model. This is enables Edge to keep track of the model's lifecycle.

```
edge model init hello-world
```

If you check your `config.yaml` file now, you should see that your model has been added. Note that you won't see anything new appear in the Google Cloud Console until after the model has been trained, which we'll do shortly.

#### Using model templates

We're going to use the [SKLearn](https://scikit-learn.org/stable/index.html) framework for this example, so let's go ahead and install that now:

```
pip install sklearn
```

And then we can generate an outline of our model training code using a template:

```
edge model template hello-world
```

You will be asked which framework you want to use, so select `sklearn`.

#### Filling in the model code

There will now be a Python script named `train.py` inside `models/hello-world`. Open this script in your favourite editor or IDE. It looks like this:

```python
from edge.train import Trainer

class MyTrainer(Trainer):
    def main(self):
        self.set_parameter("example", 123)

        # Add model training logic here

        return 0 # return your model score here

MyTrainer("hello-world-model-training").run()
```

Let's modify this to train a simple classifier:

```python
from edge.magic import Trainer
from sklearn import datasets
from sklearn.svm import SVC

class IrisTrainer(Trainer):
    def main(self):
        self.set_parameter("gamma", "scale")

        iris = datasets.load_iris()
        clf = SVC(gamma="scale")
        X, y = iris.data, iris.target_names[iris.target]

        clf.fit(X, y)

        return clf.score(X, y)

IrisTrainer("iris-svc-model").run()
```

#### Training the model

At this point you can train the model simply by running

```
python models/hello-world/train.py
```

This will run the training script locally.

# Development guide

## Python Package

### Requirements

```
pip install -r requirements-dev.txt
```

### Build

TODO

```
./setup.py build
./setup.py install
```

Or to package

```
python -m build
```

### Push to PyPi

```
twine upload dist/* --verbose
```

### Testing locally

```
mkdir my_test_project
cd my_test_project
python -m venv env/
source env/bin/activate
pip install -e <path to tool source>
```

This will install the tool locally within a venv

## Docker image

### Build

```
docker build . -t fuzzylabs/edge
```

### Push

```
docker push fuzzylabs/edge
```
