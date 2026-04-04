from fastapi import FastAPI
from broker.bus_factory import create_system_bus
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app = FastAPI()

bus = create_system_bus(client_id="api")
bus.start()


@app.post("/verify")
def verify(data: dict):
    response = bus.request("systems.certification", {
        "action": "verify_certificate",
        "payload": data
    })
    return response


@app.post("/revoke")
def revoke(data: dict):
    response = bus.request("systems.certification", {
        "action": "revoke_certificate",
        "payload": data
    })
    return response
