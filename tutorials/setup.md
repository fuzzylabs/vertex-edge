# Getting started

By the end of this guide you'll have trained and deployed a model to GCP.

## Pre-requisites


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

# Building a simple model

## Installing vertex:edge

We'll use PIP to install **vertex:edge**. Before doing this, it's a good idea to run `pip install --upgrade-pip` to ensure that you have the most recent PIP version.

To install vertex_edge, run:

```
pip install vertex-edge
```

After doing that, you should have the `edge` command available. Try running:

```
edge --help
```

**Note** that when you run `edge` for the first time, it will download a Docker image (`fuzzylabs/edge`), which might take some time to complete. All Edge commands run inside Docker.

## Initialising vertex:edge

Before you can use **vertex:edge** to train models, you'll need to initialise it. This only needs to be done once, whenever you start a new project.

```
edge init
```

The initialisation step will first verify that your GCP environment is setup correctly and it will confirm your choice of project name and region, so that you don't accidentally install things to the wrong GCP environment.

It will ask you to choose a name for a cloud storage bucket. This bucket is used for a number of things:

* Tracking the state of your project.
* Storing model assets.
* Storing versioned data.

Keep in mind that on GCP, storage bucket names are **globally unique**, so you need to choose a name that isn't already taken. For more information please see the [official GCP documentation](https://cloud.google.com/storage/docs/naming-buckets).

You might wonder what initialisation actually _does_:

* It creates a configuration file in your project directory, called `edge.yaml`. The configuration includes details about your GCP environment, the models that you have created, and the cloud storage bucket.
* And creates a _state file_. This lives in the cloud storage bucket, and it is used by **vertex:edge** to keep track of everything that it has deployed or trained.

## Training a model

### Initialisation

We're going to use the [TensorFlow](https://www.tensorflow.org) framework for this example, so let's go ahead and install that now:

```
pip install tensorflow
```

Next we initialise a new model, which makes **vertex:edge** aware of the new model.

```
edge model init hello-world
```

If you check your `config.yaml` file now, you will see that a model has been added. Note that you won't see anything new appear in the Google Cloud Console until after the model has actually been trained, which we'll do next.

### Writing a model training script

To begin with, we can generate an outline of our model training code using a template:

```
edge model template hello-world
```

You will be asked which framework you want to use, so select `tensorflow`.

There will now be a Python script named `train.py` inside `models/hello-world`. Open this script in your favourite editor or IDE. It looks like this:

```python
from edge.train import Trainer

class MyTrainer(Trainer):
    def main(self):
        self.set_parameter("example", 123)

        # Add model training logic here

        return 0 # return your model score here

MyTrainer("hello-world").run()
```

Every model training script needs to have the basic structure shown above. Let's break this down a little bit:

* We start by importing the class `Trainer` from the **vertex:edge** library.
* We define a training class. This class can have any name you like, as long as it extends `Trainer`.
* The `Trainer` class provides a method called `main`, and this is where we write all of the model training logic.
* We have the ability to set parameters and save performance metrics for experiment tracking - more on this shortly.
* At the end, we just need one more line to instantiate and run our training class.

Now let's create something a bit more interesting. A simple classifier:

```python
TODO
```

### Training and deploying the model

Now we can train the model simply by running

```
python models/hello-world/train.py
```

Which will run the training script locally - i.e. on your computer. That's fine if your model is reasonably simple, but for more compute-intensive models we want to use the on-demand compute available in Google Vertex.

The good news is that you don't need to modify the code in any way in order to train the model on Vertex, because **vertex:edge** figures out how to do package the training script and run it for you. All you run is this:

```
RUN_ON_VERTEX=True python models/hello-world/train.py
```



# Tracking experiments

TODO