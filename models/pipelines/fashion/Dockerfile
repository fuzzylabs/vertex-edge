FROM python:3.8
COPY requirements-prediction.txt requirements.txt
RUN pip install -r requirements.txt
COPY train.py train.py
COPY server.py server.py
ENTRYPOINT uvicorn server:app --host 0.0.0.0