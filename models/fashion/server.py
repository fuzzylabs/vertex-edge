import os
import dill
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.requests import Request
from google.cloud import storage
from google.cloud.storage.blob import Blob

storage_client = storage.Client()

storage_uri = os.environ.get("AIP_STORAGE_URI")

print("Getting the model dill")
# with open("model.joblib", "rb") as f:
with Blob.from_string(os.path.join(storage_uri, "model.joblib"), storage_client).open("rb") as f:
    model = dill.load(f)


async def health(request: Request):
    print("Health check")
    return PlainTextResponse("OK")


async def infer(request: Request):
    data = await request.json()
    instances = data["instances"]

    predictions = model.predict(instances)
    return JSONResponse({
        "predictions": predictions.astype(int).tolist()
    })


routes = [
    Route('/health', endpoint=health),
    Route('/infer', endpoint=infer, methods=["POST"])
]

app = Starlette(debug=True, routes=routes)
