#!/bin/bash
export GOOGLE_APPLICATION_CREDENTIALS=/root/.config/gcloud/application_default_credentials.json
gcloud config set account "$ACCOUNT"
vertex_edge.py "$@"
chown -R "$HOST_UID":"$HOST_GID" .dvc/
