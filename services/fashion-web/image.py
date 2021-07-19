from PIL import Image
import numpy as np


def prepare(file):
    with Image.open(file) as im:
        return np.array(im.resize((28, 28)).convert("L")).reshape((-1,)).astype(int).tolist()
