<p align="center"><img src="./vertex-edge-logo.png" alt="Vertex Edge Logo" height="200"/></a></p>
<p align="center">
	<img src="https://img.shields.io/github/repo-size/fuzzylabs/vertex-edge" height="20"/></a>
    <a href="https://circleci.com/gh/fuzzylabs/vertex-edge/tree/master"><img src="https://circleci.com/gh/fuzzylabs/vertex-edge/tree/master.svg?style=svg" alt="CircleCI" height="20"/></a>
</p><br/>

# Connecting the Vertices on GCP

**EDGE** is a flexible, intuitive tool for training and deploying models on [Vertex](https://cloud.google.com/vertex-ai/docs/start) (part of the [Google Cloud Platform](https://cloud.google.com)).

<!--* Supports a range of machine learning frameworks.-->
* **Seamless** training in the cloud and locally.
* **Easily adapt** your existing models to train on Vertex.
* **Plugs in to** experiment tracking and data version control.
* **Plays nicely with** CI/CD and infrastructure-as-code frameworks.

In this repository you will find:

* Source code and documentation for the tool itself.
* A step-by-step guide to training and deploying a model to Vertex using _edge_.

We've also provided a number of example models in a separate repository, see [Vertex Edge Examples](https://github.com/fuzzylabs/vertex-edge-examples).

## Table of Contents

* **[Getting started](#getting_started)** - a step-by-step guide to training and deploying a model to Vertex using _edge_.
* **[Concepts](#concepts)** - a detailed guide to the underlying MLOps concepts used in this example.

Further documentation

* **[Contributing](CONTRIBUTING.md)** - how to contribute to vertex:edge.
* **[Ready-made examples](https://github.com/fuzzylabs/vertex-edge-examples)**.

## Feedback and contributions

This is a new project and we're keen to get feedback from the community to help improve it. Please do **raise and discuss issues**, send us pull requests, and don't forget to **~~like and subscribe~~** star and fork this repo.

**If you want to contribute** then please check out our [contributions guide](CONTRIBUTING.md). We look forward to your contributions!

<a name="getting_started"></a>
# Getting started

In this guide, we'll work through the fundamentals of the vertex:edge tool. By the end you'll have trained and deployed a model to GCP.

## Pre-requisites

* [Docker](https://docs.docker.com/get-docker) (version 18 or greater).
* [gcloud command line tool](https://cloud.google.com/sdk/docs/install).
* Python, at least version 3.8.
* PIP, at least version 21.2.0 (it's a good idea to run `pip install --upgrade-pip` to ensure that you have the most recent version).
* Git

## Preparation

The very first thing you'll need is a fresh directory in which to work. For instance:

```
mkdir hello-world-vertex
cd hello-world-vertex
```

You'll need to initialise this directory as a Git repository as well:

```
git init
```

## Setting up GCP environment

Now you'll need a [GCP account](https://cloud.google.com), so sign up for one if you haven't already done so.

Within your GCP account, [create a new project](https://cloud.google.com/resource-manager/docs/creating-managing-projects). Take a note of the project ID (you'll be able to view this in the Google Cloud console with the project selection dialog). The project ID won't necessarily match the name that you chose for the project; sometimes GCP might append some numbers to the original name.

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

You'll also need to configure a region. Please see the [GCP documentation](https://cloud.google.com/vertex-ai/docs/general/locations#feature-availability) to understand which regions are available for Vertex.

```
gcloud config set compute/region <region name>
```

**Note** `gcloud` might ask you if you want to enable the Google Compute API on the project. If so, choose `y`.

Finally, you need to get application default credentials by running:

```
gcloud auth application-default login
```

## Installing vertex:edge

We'll use PIP to install _edge_:

```
pip install vertex-edge
```

After doing that, you should have the `edge` command available. Try running:

```
edge --help
```

**Note** that when you run `edge` for the first time, it will download a Docker image (`fuzzylabs/edge`). All Edge commands run inside Docker.

## Initialising vertex:edge

Before you can use vertex:edge to train models, you'll need to initialise it (this only needs to be done once).

```
edge init
```

The initialisation step will first check that your GCP environment is setup correctly and it will confirm your choice of project name and region, so that you don't accidentally install things to the wrong GCP environment.

It will ask you to choose a name for a cloud storage bucket. This bucket is used for tracking the vertex:edge state, for data version control and for model assets. Keep in mind that on GCP, storage bucket names are **globally unique**, so you might find that the name you want to use is already taken (in which case vertex:edge will give you an error message). For more information please see the [official GCP documentation](https://cloud.google.com/storage/docs/naming-buckets).

You might wonder what initialisation actually _does_. It sets up two things:

* Creates a configuration file in your project directory, called `edge.yaml`. The configuration includes details about your GCP environment, the models that you have registered, and the cloud storage bucket.
* Creates a _state file_. The state file lives in the cloud storage bucket, and its purpose is to make sure that only one person can modify the GCP environment at any one time.

## Setting up data version control

Don't worry, you'll get to actually train a model very soon! But there's one more thing we need, and that's data version control.

Just as we use Git to track the history of our model code, we want to track data as it changes. It's important to have this set up from the very start, because:

* It will be easier for a team to share data while ensuring that everybody is working with the same version of that data.
* It allows us to track changes over time.
* We can link every experiment and deployed model to a specific data version.

There are many different tools for data versioning; the one we use [DVC](https://dvc.org) which, itself stands for Data Version Control.

To set it up, run

```
edge dvc init
```

This does two things:

* Configures DVC locally so that you can version your data.
* Sets up remote storage using a Google Cloud Bucket so that versioned data is stored centrally.

At this point, if you're not already familiar with DVC, it may be a good idea to familiarise yourself with this a little before continuing by reading the [DVC official documentation](https://dvc.org/doc). Of course, if you'd prefer to defer that to later, you can carry on to training and deploying the model.

## Training a model

Once you've set up DVC, you're ready to train a simple `hello world` model. This model won't do anything really useful, but it serves to demonstrate the building blocks and enable you to build _serious_ models.

First, let's make an empty directory to house your model training code:

```
mkdir -p models/hello-world
```

Next, initialise the model. This is enables vertex:edge to keep track of the model's lifecycle.

```
edge model init hello-world
```

If you check your `config.yaml` file now, you should see that your model has been added. Note that you won't see anything new appear in the Google Cloud Console until after the model has been trained, which we'll do shortly.

We're going to use the [SKLearn](https://scikit-learn.org/stable/index.html) framework for this example, so let's go ahead and install that now:

```
pip install sklearn
```

### Filling in the model code

We're going to use a feature of SKLearn called a Dummy Classifier, which behaves just like a real classifier, and allows us to create a fake model for the purposes of testing.

Take a look at this code snippet. This is the raw training script, without any embellishments.

```python
import numpy as np
from sklearn.dummy import DummyClassifier

# The strategy tells the DummyClassfier how to behave
# Model training generally involves a multitude of parameters,
# In this case, strategy is our sole parameter
strategy = "most_frequent"

# Define some training data
X = np.array([-1, 1, 1, 1])
y = np.array([0, 1, 1, 1])

# Train a classifier
dummy_clf = DummyClassifier(strategy=strategy)
dummy_clf.fit(X, y)

# Capture the training score
print(f"Training score {dummy_clf.score(X, y)}")
```

We can run the above script locally and get a model out of it. Vertex:Edge provides an API that makes it simple to turn our training script into one that can run both locally and on Vertex.

To set this up, we need to define two functions:

* A configuration function that sets up the model's parameters.
* A training function that has the actual training logic.

That's all there is to it! of course, for your needs, you may want to define more functions of your own, but these are the only things you _have_ to define, so that the tool can figure out how to run your model training script.

Below is the complete `hello world` example. Using your favourite editor, copy this code into a file named `train.py` inside the model directory created earlier.

```python
from edge.training.training import *
from edge.training.sklearn.utils import save_results

from sacred import Experiment

import numpy as np
from sklearn.dummy import DummyClassifier

_config, state = get_config_and_state()

ex = Experiment("hello-world-model-training", save_git_info=False)

@ex.config
def cfg():
    strategy = "most_frequent"
    model_name = "hello-world"
    is_vertex = False


@ex.automain
@vertex_wrapper(_config, state)
def run(
        _run,
        strategy,
        model_output_dir="./",
):
    X = np.array([-1, 1, 1, 1])
    y = np.array([0, 1, 1, 1])
    dummy_clf = DummyClassifier(strategy=strategy)
    dummy_clf.fit(X, y)

    metrics = {
        "score": dummy_clf.score(X, y)
    }

    save_results(dummy_clf, metrics, model_output_dir)
```

There are a few additions to the original code:

At the end of that `run` function, we call `save_results`. This function is provided by the Vertex:Edge library and it will ensure that the model gets saved.

Near the top of the script, we have this line `ex = Experiment("hello-world-model-training", save_git_info=False)`. We're not introducing experiment tracking just yet; that's for later on. For now all you need to know is that every time the training script is executed, that counts as an experiment, and a bit later on, you'll be able to record and review these experiments.

### Training the model

At this point you can train the model simply by running

```
python models/hello-world/train.py with is_vertex=False
```

And this will run the training script locally. As you can imagine, if you were to set `is_vertex=True` then will run the script on Vertex. However, it's better to do the training via a DVC pipeline.

This is because:

* Pipelines can have multiple steps. For instance, we might want a data preparation step that runs before the model training script,
* It gives us access to data versioning without the code in the script having to be aware of data versioning,
* And a pipeline represents a well-defined workflow that can be easily reproduced.

<!-- TODO: add the pipeline file / replace all with templating -->

First, let's jump in to a shell using `edge`:

```
edge bash
```

And within the Bash shell run

```
dvc repro models/hello-world/dvc.yaml
```

Then `dvc repro` runs the pipeline itself. This might take a little while to run, but you'll see periodic status updates as it progresses. You can also view the [job in progress in the Google Cloud Console](https://console.cloud.google.com/vertex-ai/training/custom-jobs).

At the end of training remember to exit the Bash session with `exit`.

## Deploying your trained model

Having trained the model, you should see it listed in the [Google Cloud console under 'models'](https://console.cloud.google.com/vertex-ai/models). However, the model hasn't yet been deployed, so we can't interact with it.

Deployment is done with just one command:

```
edge model deploy
```

To interact with a model, you need to know its _endpoint_. You can get hold of the endpoint associated with the model by running

```
edge model get-endpoint
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
