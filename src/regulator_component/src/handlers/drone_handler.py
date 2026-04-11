# handlers/drone_handler.py
import logging
from datetime import datetime

from ..models import DroneRequest, DroneResult
from ..certificate_manager import CertificateManager
from ..broker_client import BrokerClient
from ..config import Config

logger = logging.getLogger(__name__)


class DroneHandler:
    def __init__(self, cert_manager: CertificateManager, broker: BrokerClient):
        self.cert_manager = cert_manager
        self.broker = broker

    async def handle(self, message: dict):
        try:
            req = DroneRequest(**message)
            logger.info(f"Processing drone registration {req.request_id}")

            firmware_cert_id = req.firmware.get("certificate_id")
            if not firmware_cert_id:
                result = DroneResult(
                    request_id=req.request_id,
                    timestamp=datetime.utcnow(),
                    status="REJECTED",
                    drone=None,
                    certificate=None
                )
                await self.broker.publish(Config.TOPIC_DRONE_RESULT, result.model_dump_json())
                logger.warning(f"Drone {req.request_id}: missing firmware certificate")
                return

            fw_cert = self.cert_manager.get_certificate(firmware_cert_id)
            if not fw_cert or not self.cert_manager.verify_certificate(fw_cert):
                result = DroneResult(
                    request_id=req.request_id,
                    timestamp=datetime.utcnow(),
                    status="REJECTED",
                    drone=None,
                    certificate=None
                )
                await self.broker.publish(Config.TOPIC_DRONE_RESULT, result.model_dump_json())
                logger.warning(f"Drone {req.request_id}: invalid firmware certificate {firmware_cert_id}")
                return

            cert = self.cert_manager.create_certificate(
                subject_type="drone",
                subject_id=req.drone.get("serial_number", req.request_id),
                security_goals=["DRONE-INTEGRITY", "DRONE-AUTH"]
            )

            reg_number = f"RU-BAS-{cert.certificate_id[-8:]}"

            result = DroneResult(
                request_id=req.request_id,
                timestamp=datetime.utcnow(),
                status="APPROVED",
                drone={
                    "serial_number": req.drone.get("serial_number"),
                    "model": req.drone.get("model"),
                    "registration_number": reg_number
                },
                certificate=cert.model_dump()
            )
            await self.broker.publish(Config.TOPIC_DRONE_RESULT, result.model_dump_json())
            logger.info(f"Drone {req.request_id} registered with {cert.certificate_id}")
        except Exception as e:
            logger.error(f"Error processing drone registration: {e}", exc_info=True)
