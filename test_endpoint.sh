#!/bin/bash

ENDPOINT=$(./edge.sh model get-endpoint)
curl \
-X POST \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
https://europe-west4-aiplatform.googleapis.com/v1/${ENDPOINT}:predict \
-d "@test_payload.json"