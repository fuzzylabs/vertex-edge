#!/bin/bash

mkdir -p data/fashion-mnist
curl http://fashion-mnist.s3-website.eu-central-1.amazonaws.com/train-images-idx3-ubyte.gz -o data/fashion-mnist/train-images-idx3-ubyte.gz
curl http://fashion-mnist.s3-website.eu-central-1.amazonaws.com/train-labels-idx1-ubyte.gz -o data/fashion-mnist/train-labels-idx1-ubyte.gz
curl http://fashion-mnist.s3-website.eu-central-1.amazonaws.com/t10k-images-idx3-ubyte.gz -o data/fashion-mnist/t10k-images-idx3-ubyte.gz
curl http://fashion-mnist.s3-website.eu-central-1.amazonaws.com/t10k-labels-idx1-ubyte.gz -o data/fashion-mnist/t10k-labels-idx1-ubyte.gz

dvc add data/fashion-mnist/*.gz