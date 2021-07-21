#!/bin/bash
ACCOUNT=$(gcloud config get-value account)
HOST_UID=$(id -u)
HOST_GID=$(id -g)
docker run -it \
 -v "$(pwd)":/project/ \
 -v ~/.config/gcloud/:/root/.config/gcloud/ \
 -e ACCOUNT="$ACCOUNT" -e HOST_UID="$HOST_UID" -e HOST_GID="$HOST_GID" \
 --entrypoint bash fuzzylabs/edge ./edge_docker_entrypoint.sh "$@"
