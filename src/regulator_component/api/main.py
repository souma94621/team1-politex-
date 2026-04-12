from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from broker import BrokerService
from config import Config

app = FastAPI()
broker = BrokerService()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------- MODELS --------

class FirmwareRequest(BaseModel):
    request_id: str
    drone_type: str
    firmware: dict


class OperatorRequest(BaseModel):
    message_id: str
    operator_id: str


class InsurerRequest(BaseModel):
    message_id: str
    insurer_id: str


# -------- ROUTES --------

@app.post("/firmware")
async def firmware(req: FirmwareRequest):
    return await broker.send_and_wait(
        Config.TOPIC_FIRMWARE_REQUEST,
        Config.TOPIC_FIRMWARE_RESULT,
        req.dict()
    )


@app.post("/operator")
async def operator(req: OperatorRequest):
    return await broker.send_and_wait(
        Config.TOPIC_OPERATOR_REQUEST,
        Config.TOPIC_OPERATOR_RESULT,
        req.dict()
    )


@app.post("/insurer")
async def insurer(req: InsurerRequest):
    return await broker.send_and_wait(
        Config.TOPIC_INSURER_REQUEST,
        Config.TOPIC_INSURER_RESPONSE,
        req.dict()
    )