import time

from main.core.gateways.kafka import Kafka
from main.dependencies.kafka import get_kafka_instance
from main.enum import EnvironmentVariables
from main.routers import bond_funds_routers

from dotenv import load_dotenv

from fastapi import Depends, FastAPI, Request

load_dotenv()


app = FastAPI(title='Kafka Publisher API')
kafka_server = Kafka(
    topic=EnvironmentVariables.KAFKA_TOPIC_NAME.get_env(),
    port=EnvironmentVariables.KAFKA_PORT.get_env(),
    servers=EnvironmentVariables.KAFKA_SERVER.get_env(),
)


async def lifespan(app: FastAPI):
    # Startup event
    await kafka_server.aioproducer.start()

    # Shutdown event
    yield

    await kafka_server.aioproducer.stop()

# Use the lifespan event handler
app = FastAPI(title='Kafka Publisher API', lifespan=lifespan)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.get('/')
def get_root():
    return {'message': 'API is running...'}


app.include_router(
    bond_funds_routers.router,
    prefix="/producer",
    tags=["producer"],
    dependencies=[Depends(get_kafka_instance)],
)
