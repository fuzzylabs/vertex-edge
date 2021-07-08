from train import train_model
from sklearn.base import ClassifierMixin


def test_train_model():
    """
    Test that training function returns an sklearn classifier

    :return:
    """
    X = [[0], [1], [2], [3]]
    y = [0, 0, 1, 1]
    model = train_model((X, y), 3)
    assert isinstance(model, ClassifierMixin)
