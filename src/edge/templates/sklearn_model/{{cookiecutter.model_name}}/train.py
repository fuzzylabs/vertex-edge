from edge.train import Trainer

class MyTrainer(Trainer):
    def main(self):
        self.set_parameter("example", 123)

        # Add model training logic here

        return 0 # return your model score here

MyTrainer("{{cookiecutter.model_name}}").run()
