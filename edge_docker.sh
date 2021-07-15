#!/bin/bash
ACCOUNT=$(gcloud config get-value account)

docker run -it \
 -v "$(pwd)":/project/ \
 -v ~/.config/gcloud/:/root/.config/gcloud/ \
 -e ACCOUNT="$ACCOUNT" \
 --entrypoint bash edge ./edge_docker_entrypoint.sh "$@"