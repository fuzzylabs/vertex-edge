#!/bin/bash

ENDPOINT=$(./edge.sh model get-endpoint)
REGION=$(./edge.sh config get-region)
curl \
-X POST \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
"https://${REGION}-aiplatform.googleapis.com/v1/${ENDPOINT}:predict" \
-d "@test_payload.json"