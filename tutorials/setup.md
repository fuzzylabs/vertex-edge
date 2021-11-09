# vertex:edge setup

In this tutorial you'll see how to set up a new project using vertex:edge.

## Preparation

The very first thing you'll need is a fresh directory in which to work. For instance:

```
mkdir hello-world-vertex
cd hello-world-vertex
```

## Setting up GCP environment

Now you'll need a [GCP account](https://cloud.google.com), so sign up for one if you haven't already done so.

Then within your GCP account, [create a new project](https://cloud.google.com/resource-manager/docs/creating-managing-projects). Take a note of the project ID; you'll be able to view this in the Google Cloud console with the project selection dialog). Note that the project ID won't necessarily match the name that you chose for the project, as GCP often appends some digits to the end of the name.

Finally make sure you have [enabled billing](https://cloud.google.com/billing/docs/how-to/modify-project) for your new project too.

## Authenticating with GCP

If you haven't got the `gcloud` command line tool, [install it now](https://cloud.google.com/sdk/docs/install).

And then authenticate by running:

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

Before you can use **vertex:edge** to train models, you'll need to initialise your project. This only needs to be done once, whenever you start a new project.

Inside your project directory, run

```
edge init
```

As part of the initialisation process, vertex:edge will first verify that your GCP environment is setup correctly and it will confirm your choice of project name and region, so that you don't accidentally install things to the wrong GCP environment.

It will ask you to choose a name for a cloud storage bucket. This bucket is used for a number of things:

* Tracking the state of your project.
* Storing model assets.
* Storing versioned data.

Keep in mind that on GCP, storage bucket names are **globally unique**, so you need to choose a name that isn't already taken. For more information please see the [official GCP documentation](https://cloud.google.com/storage/docs/naming-buckets).

You might wonder what initialisation actually _does_:

* It creates a configuration file in your project directory, called `edge.yaml`. The configuration includes details about your GCP environment, the models that you have created, and the cloud storage bucket.
* And creates a _state file_. This lives in the cloud storage bucket, and it is used by **vertex:edge** to keep track of everything that it has deployed or trained.

## Next steps

After all of the above, you'll have a new project directory `hello-world-vertex`, which will contain a configuration file `edge.yaml`. You'll also have a GCP project, inside which there will be a cloud storage bucket with a name that matches what you chose during `edge init`.

You're now ready to train and deploy a model. See the [next tutorial](train_deploy.md) to learn how.
