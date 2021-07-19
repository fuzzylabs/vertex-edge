import io
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse
from starlette.templating import Jinja2Templates
from google.cloud.aiplatform import Endpoint
from image import prepare
import os

endpoint_id = os.environ.get("ENDPOINT_ID")

templates = Jinja2Templates(directory="templates")

endpoint = Endpoint(endpoint_name=endpoint_id, project="fuzzylabs", location="europe-west4")

class_mapping = {
    0: "T-shirt/top",
    1: "Trouser",
    2: "Pullover",
    3: "Dress",
    4: "Coat",
    5: "Sandal",
    6: "Shirt",
    7: "Sneaker",
    8: "Bag",
    9: "Ankle boot",
}


async def homepage(request):
    return templates.TemplateResponse("index.html", {"request": request})


async def infer(request):
    form = await request.form()
    contents = await form["img"].read()
    img = prepare(io.BytesIO(contents))

    print(type(img))
    prediction = endpoint.predict(instances=[img])
    print(prediction)
    return JSONResponse({"class": class_mapping[int(prediction.predictions[0])]})


routes = [Route("/", endpoint=homepage), Route("/infer", endpoint=infer, methods=["POST"])]

app = Starlette(debug=True, routes=routes)
