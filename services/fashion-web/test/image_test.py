from image import prepare
import numpy as np


def test_prepare():
    """
    Test that prepared input image is an array of correct size and valid values
    :return:
    """
    img = prepare("test/test-t-shirt.jpeg")
    assert len(img) == 28*28
    assert np.all(np.array(img) >= 0)
    assert np.all(np.array(img) <= 255)
