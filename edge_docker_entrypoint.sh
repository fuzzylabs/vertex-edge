#!/bin/bash
export GOOGLE_APPLICATION_CREDENTIALS=/root/.config/gcloud/application_default_credentials.json
gcloud config set component_manager/disable_update_check true &> /dev/null
gcloud config set account "$ACCOUNT" &> /dev/null

if [[ $1 == "bash" ]]
then
   bash
else
    vertex_edge.py "$@"
fi

chown -R "$HOST_UID":"$HOST_GID" .dvc/
chown -R "$HOST_UID":"$HOST_GID" data/
