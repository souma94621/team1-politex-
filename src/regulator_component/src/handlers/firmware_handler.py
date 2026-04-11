# handlers/firmware_handler.py
import logging
import json
from datetime import datetime

from ..models import FirmwareRequest, FirmwareResult
from ..certificate_manager import CertificateManager
from ..security_test_runner import SecurityTestRunner
from ..coverage_controller import CoverageController
from ..broker_client import BrokerClient
from ..config import Config

logger = logging.getLogger(__name__)


class FirmwareHandler:
    def __init__(self, cert_manager: CertificateManager, test_runner: SecurityTestRunner,
                 coverage_controller: CoverageController, broker: BrokerClient):
        self.cert_manager = cert_manager
        self.test_runner = test_runner
        self.coverage_controller = coverage_controller
        self.broker = broker

    async def handle(self, message):
        try:
            if isinstance(message, (str, bytes)):
                data = json.loads(message)
            else:
                data = message

            logger.info(f"[DEBUG] FirmwareHandler received: {data}")

            req = FirmwareRequest(**data)
            logger.info(f"--- [START] Processing firmware request: {req.request_id} ---")

            logger.info(f"Running security tests for {req.drone_type}...")
            test_result = await self.test_runner.run_tests(req.firmware)

            if not test_result.get("passed", False):
                logger.warning(f"!!! SECURITY ALERT: Firmware {req.request_id} rejected !!!")
                result = FirmwareResult(
                    request_id=req.request_id,
                    timestamp=datetime.now(),
                    status="REJECTED",
                    certificate=None
                )
                await self.broker.publish(Config.TOPIC_FIRMWARE_RESULT, result.model_dump_json())
                return

            logger.info("Security tests passed. Generating certificate...")
            cert = self.cert_manager.create_certificate(
                subject_type="firmware",
                subject_id=req.firmware.get("commit_hash", req.request_id),
                security_goals=["FW-SEC-01", "FW-SEC-02", "FW-SEC-05"]
            )

            result = FirmwareResult(
                request_id=req.request_id,
                timestamp=datetime.now(),
                status="CERTIFIED",
                certificate=cert.model_dump()
            )

            response_json = result.model_dump_json()
            await self.broker.publish(Config.TOPIC_FIRMWARE_RESULT, response_json)
            logger.info(f"+++ [SUCCESS] Firmware {req.request_id} certified as {cert.certificate_id} +++")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON message: {e}")
        except Exception as e:
            logger.error(f"Error in FirmwareHandler: {e}", exc_info=True)
