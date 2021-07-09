#!/bin/bash
export GOOGLE_APPLICATION_CREDENTIALS=/root/.config/gcloud/application_default_credentials.json
gcloud config set account "$ACCOUNT"
python edge.py setup