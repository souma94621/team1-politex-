# src/regulator_component/src/handlers/firmware_handler.py
import json
import logging
from datetime import datetime

from models import FirmwareRequest, FirmwareResult
from certificate_manager import CertificateManager
from security_test_runner import SecurityTestRunner
from coverage_controller import CoverageController
from broker_client import BrokerClient
from config import Config
from goals_check import GoalsCheck
from managers.ci_service import ContinuousIntegration  # NEW

logger = logging.getLogger(__name__)


class FirmwareHandler:
    def __init__(
        self,
        cert_manager: CertificateManager,
        test_runner: SecurityTestRunner,
        coverage_controller: CoverageController,
        broker: BrokerClient,
        goals_check: GoalsCheck,
        ci_service: ContinuousIntegration   # NEW
    ):
        self.cert_manager = cert_manager
        self.test_runner = test_runner
        self.coverage_controller = coverage_controller
        self.broker = broker
        self.goals_check = goals_check
        self.ci_service = ci_service

    async def handle(self, message: dict):
        try:
            if isinstance(message, (str, bytes)):
                data = json.loads(message)
            else:
                data = message

            req = FirmwareRequest(**data)
            logger.info(f"Processing firmware request {req.request_id}")

            # Получаем цели безопасности для прошивки
            security_goals = self.goals_check.get_goals_for_system("firmware")
            if not security_goals:
                logger.warning("No security goals, using defaults")
                security_goals = ["FW-SEC-01", "FW-SEC-02", "FW-SEC-05"]

            # Запуск реальных тестов через CI
            test_result = await self.test_runner.run_tests(data)

            if not test_result.get("passed", False):
                result = FirmwareResult(
                    request_id=req.request_id,
                    timestamp=datetime.utcnow(),
                    status="REJECTED",
                    certificate={
                        "reason": "Security tests failed",
                        "test_details": test_result.get("details", {})
                    }
                )
                await self.broker.publish(Config.TOPIC_FIRMWARE_RESULT, json.loads(result.model_dump_json()))
                logger.warning(f"Firmware {req.request_id} REJECTED: tests failed")
                return

            # Проверка покрытия (можно тоже реальную)
            repo_url = req.firmware.get("repository_url", "")
            commit_hash = req.firmware.get("commit_hash", req.request_id)
            coverage = await self.coverage_controller.get_coverage(repo_url, commit_hash)

            # Генерация ID сертификата через CI
            cert_id = self.ci_service.generate_certificate_id("firmware", commit_hash)

            # Создание сертификата
            cert = self.cert_manager.create_certificate(
                subject_type="firmware",
                subject_id=commit_hash,
                security_goals=security_goals
            )

            result = FirmwareResult(
                request_id=req.request_id,
                timestamp=datetime.utcnow(),
                status="CERTIFIED",
                certificate={
                    "certificate_id": cert.certificate_id,
                    "firmware": {
                        "version": req.firmware.get("version", ""),
                        "commit_hash": commit_hash,
                    },
                    "drone_type": req.drone_type,
                    "requirements_checked": security_goals,
                    "coverage_percent": coverage,
                    "digital_signature": cert.digital_signature,
                    "ci_request_id": test_result.get("details", {}).get("request_id")
                }
            )

            await self.broker.publish(Config.TOPIC_FIRMWARE_RESULT, json.loads(result.model_dump_json()))
            logger.info(f"Firmware {req.request_id} CERTIFIED with {cert.certificate_id}")

        except Exception as e:
            logger.error(f"Error in FirmwareHandler: {e}", exc_info=True)
