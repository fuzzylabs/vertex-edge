from mnist import MNIST
import dill

mnist_data = MNIST('../../../data/fashion-mnist', gz=True)

train_images, train_labels = mnist_data.load_training()
test_images, test_labels = mnist_data.load_testing()

with open("../../../data/fashion-mnist/train.pickle", "wb") as f:
    dill.dump((train_images, train_labels), f)

with open("../../../data/fashion-mnist/test.pickle", "wb") as f:
    dill.dump((test_images, test_labels), f)

