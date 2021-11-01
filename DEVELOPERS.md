# Development guide

## Python Package

### Requirements

```
pip install -r requirements-dev.txt
```

### Build

TODO

```
./setup.py build
./setup.py install
```

Or to package

```
python -m build
```

### Push to PyPi

```
twine upload dist/* --verbose
```

### Testing locally

```
mkdir my_test_project
cd my_test_project
python -m venv env/
source env/bin/activate
pip install -e <path to tool source>
```

This will install the tool locally within a venv

## Docker image

### Build

```
docker build . -t fuzzylabs/edge
```

### Push

```
docker push fuzzylabs/edge
```

