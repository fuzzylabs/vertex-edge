# Training a model

In this tutorial you'll be able to train and deploy a TensorFlow model to Google Vertex using the vertex:edge command line tool and Python library.

Before following this tutorial, you should have already setup a GCP project and initialised vertex:edge. See the [setup tutorial](setup.md) for more information.

## Initialisation

We're going to use the [TensorFlow](https://www.tensorflow.org) framework for this example, so let's go ahead and install that now:

```
pip install tensorflow
```

Next we initialise a new model, which makes **vertex:edge** aware that there is a new model.

```
edge model init hello-world
```

If you check your `config.yaml` file now, you will see that a model has been added to the `models` section:

```yaml
models:
  hello-world:
    endpoint_name: hello-world-endpoint
    name: hello-world
    serving_container_image_uri: europe-docker.pkg.dev/vertex-ai/prediction/tf2-cpu.2-6:latest
    training_container_image_uri: europe-docker.pkg.dev/vertex-ai/training/tf-cpu.2-6:latest
```

Note that you won't see anything new appear in the Google Cloud Console until after the model has actually been trained, which we'll do next.

## Writing a model training script

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

## Training and deploying the model

Now we can train the model simply by running

```
python models/hello-world/train.py
```

Which will run the training script locally - i.e. on your computer. That's fine if your model is reasonably simple, but for more compute-intensive models we want to use the on-demand compute available in Google Vertex.

The good news is that you don't need to modify the code in any way in order to train the model on Vertex, because **vertex:edge** figures out how to do package the training script and run it for you. All you run is this:

```
RUN_ON_VERTEX=True python models/hello-world/train.py
```
