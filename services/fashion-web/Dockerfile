FROM python:3.8
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY templates/ templates/
COPY server.py server.py
ENTRYPOINT uvicorn server:app --host 0.0.0.0 --port 8080