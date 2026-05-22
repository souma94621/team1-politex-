"""
Decision Engine — компонент принятия решений (шаблон A.2).
Отделён от технического исполнения (CertificateManager, CI, и т.д.).
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from ..models import FirmwareRequest, DroneRequest, SystemRegistrationRequest
from .certificate_manager import CertificateManager
from .ci_service import ContinuousIntegration
from .coverage_controller import CoverageController
from ..goals_check import GoalsCheck

logger = logging.getLogger(__name__)


class DecisionEngine:
    """
    Единый движок принятия решений.
    Хендлеры вызывают его методы, он возвращает готовый ответ.
    """

    def __init__(
        self,
        cert_manager: CertificateManager,
        ci_service: ContinuousIntegration,
        coverage_controller: CoverageController,
        goals_check: GoalsCheck
    ):
        self.cert_manager = cert_manager
        self.ci_service = ci_service
        self.coverage_controller = coverage_controller
        self.goals_check = goals_check

    async def decide_firmware_certification(self, raw_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Принимает решение о сертификации прошивки.
        Возвращает готовый ответ для публикации.
        """
        try:
            request = FirmwareRequest(**raw_message)
            logger.info(f"DecisionEngine: processing firmware {request.request_id}")

            # 1. Получить цели безопасности
            security_goals = self.goals_check.get_goals_for_system("firmware")
            if not security_goals:
                security_goals = ["FW-SEC-01", "FW-SEC-02", "FW-SEC-05"]

            # 2. Запустить CI-тесты
            test_result = await self.ci_service.process_firmware(request)
            if not test_result.get("passed", False):
                return {
                    "request_id": request.request_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "REJECTED",
                    "certificate": None,
                    "reason": "Security tests failed",
                    "test_details": test_result.get("test_results", [])
                }

            # 3. Проверить покрытие (если настроено)
            repo_url = request.firmware.get("repository_url", "")
            commit_hash = request.firmware.get("commit_hash", request.request_id)
            coverage = await self.coverage_controller.get_coverage(repo_url, commit_hash)

            # 4. Принять решение о выдаче сертификата
            cert = self.cert_manager.create_certificate(
                subject_type="firmware",
                subject_id=commit_hash,
                security_goals=security_goals
            )

            # 5. Сформировать ответ
            return {
                "request_id": request.request_id,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "CERTIFIED",
                "certificate": {
                    "certificate_id": cert.certificate_id,
                    "firmware": {
                        "version": request.firmware.get("version", ""),
                        "commit_hash": commit_hash,
                    },
                    "drone_type": request.drone_type,
                    "requirements_checked": security_goals,
                    "coverage_percent": coverage,
                    "digital_signature": cert.digital_signature,
                }
            }

        except Exception as e:
            logger.error(f"DecisionEngine firmware error: {e}", exc_info=True)
            return {
                "request_id": raw_message.get("request_id"),
                "timestamp": datetime.utcnow().isoformat(),
                "status": "ERROR",
                "certificate": None,
                "reason": str(e)
            }

    async def decide_drone_registration(self, raw_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Принимает решение о регистрации дрона.
        Возвращает готовый ответ для публикации.
        """
        try:
            request = DroneRequest(**raw_message)
            logger.info(f"DecisionEngine: processing drone {request.request_id}")

            # 1. Проверить сертификат прошивки
            firmware_cert_id = request.firmware.get("certificate_id")
            if not firmware_cert_id:
                return {
                    "request_id": request.request_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "REJECTED",
                    "drone": None,
                    "certificate": None,
                    "reason": "Missing firmware certificate_id"
                }

            fw_cert = self.cert_manager.get_certificate(firmware_cert_id)
            if not fw_cert or not self.cert_manager.verify_certificate(fw_cert):
                return {
                    "request_id": request.request_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "REJECTED",
                    "drone": None,
                    "certificate": None,
                    "reason": "Invalid or missing firmware certificate"
                }

            # 2. Создать сертификат дрона
            serial_number = request.drone.get("serial_number", request.request_id)
            cert = self.cert_manager.create_certificate(
                subject_type="drone",
                subject_id=serial_number,
                security_goals=["DRONE-INTEGRITY", "DRONE-AUTH"],
                extra_fields={"firmware_certificate_id": firmware_cert_id}
            )

            reg_number = f"RU-BAS-{cert.certificate_id[-8:]}"

            return {
                "request_id": request.request_id,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "APPROVED",
                "drone": {
                    "serial_number": serial_number,
                    "model": request.drone.get("model"),
                    "registration_number": reg_number,
                },
                "certificate": {
                    "certificate_id": cert.certificate_id,
                    "issued_by": "REGULATOR",
                    "digital_signature": cert.digital_signature,
                }
            }

        except Exception as e:
            logger.error(f"DecisionEngine drone error: {e}", exc_info=True)
            return {
                "request_id": raw_message.get("request_id"),
                "timestamp": datetime.utcnow().isoformat(),
                "status": "ERROR",
                "reason": str(e)
            }

    async def decide_system_certification(self, raw_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Принимает решение о сертификации внешней системы.
        """
        try:
            system_id = raw_message.get("system_id")
            system_type = raw_message.get("system_type", "system")

            if not system_id:
                return {
                    "status": "REJECTED",
                    "reason": "Missing system_id"
                }

            security_goals = self.goals_check.get_goals_for_system(system_type)
            if not security_goals:
                security_goals = ["SYSTEM-INTEGRITY"]

            cert = self.cert_manager.create_certificate(
                subject_type="system",
                subject_id=system_id,
                security_goals=security_goals
            )

            return {
                "system_id": system_id,
                "certificate_id": cert.certificate_id,
                "issued_at": cert.issued_at.isoformat(),
                "valid_until": cert.valid_until.isoformat(),
                "security_goals": security_goals,
                "digital_signature": cert.digital_signature,
                "status": "CERTIFIED"
            }

        except Exception as e:
            logger.error(f"DecisionEngine system error: {e}", exc_info=True)
            return {
                "system_id": raw_message.get("system_id"),
                "status": "ERROR",
                "reason": str(e)
            }

    async def decide_owner_transfer(self, raw_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Принимает решение о передаче права собственности на дрона.
        """
        try:
            drone_id = raw_message.get("drone_id")
            new_owner_id = raw_message.get("new_owner_id")

            if not drone_id or not new_owner_id:
                return {
                    "drone_id": drone_id,
                    "status": "REJECTED",
                    "reason": "Missing drone_id or new_owner_id"
                }

            # Найти сертификат дрона
            cert = self.cert_manager.find_certificate_by_subject("drone", drone_id)
            if not cert or not self.cert_manager.verify_certificate(cert):
                return {
                    "drone_id": drone_id,
                    "status": "REJECTED",
                    "reason": "Drone certificate not found or invalid"
                }

            # Отозвать старый сертификат
            self.cert_manager.revoke_certificate(cert.certificate_id)

            # Создать новый с новым владельцем
            new_cert = self.cert_manager.create_certificate(
                subject_type="drone",
                subject_id=drone_id,
                security_goals=cert.security_goals,
                extra_fields={"owner_id": new_owner_id, "previous_certificate": cert.certificate_id}
            )

            return {
                "drone_id": drone_id,
                "status": "TRANSFERRED",
                "old_certificate_id": cert.certificate_id,
                "new_certificate_id": new_cert.certificate_id,
                "new_owner_id": new_owner_id,
                "valid_until": new_cert.valid_until.isoformat()
            }

        except Exception as e:
            logger.error(f"DecisionEngine transfer error: {e}", exc_info=True)
            return {
                "drone_id": raw_message.get("drone_id"),
                "status": "ERROR",
                "reason": str(e)
            }

    async def decide_operator_status(self, raw_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Принимает решение о статусе сертификата дрона для оператора.
        """
        try:
            operator_id = raw_message.get("operator_id")
            drone_id = raw_message.get("drone_id")
            request_id = raw_message.get("request_id")

            if not operator_id or not drone_id:
                return {
                    "request_id": request_id,
                    "operator_id": operator_id,
                    "drone_id": drone_id,
                    "certificate_status": "error",
                    "reason": "Missing operator_id or drone_id"
                }

            drone_cert = self.cert_manager.find_certificate_by_subject("drone", drone_id)
            if not drone_cert:
                return {
                    "request_id": request_id,
                    "operator_id": operator_id,
                    "drone_id": drone_id,
                    "certificate_status": "invalid",
                    "reason": "Drone not found or has no certificate"
                }

            is_valid = self.cert_manager.verify_certificate(drone_cert)

            # Получить информацию о прошивке
            firmware_info = None
            if drone_cert.extra and "firmware_certificate_id" in drone_cert.extra:
                fw_cert = self.cert_manager.get_certificate(drone_cert.extra["firmware_certificate_id"])
                if fw_cert:
                    firmware_info = {
                        "certificate_id": fw_cert.certificate_id,
                        "subject_id": fw_cert.subject_id,
                        "valid_until": fw_cert.valid_until.isoformat()
                    }

            return {
                "request_id": request_id,
                "operator_id": operator_id,
                "drone_id": drone_id,
                "timestamp": datetime.utcnow().isoformat(),
                "certificate_status": "valid" if is_valid else "invalid",
                "reason": None if is_valid else "Certificate invalid or revoked",
                "drone_certificate": {
                    "certificate_id": drone_cert.certificate_id,
                    "issued_at": drone_cert.issued_at.isoformat(),
                    "valid_until": drone_cert.valid_until.isoformat(),
                    "security_goals": drone_cert.security_goals
                },
                "firmware_certificate": firmware_info,
                "owner_id": drone_cert.owner_id
            }

        except Exception as e:
            logger.error(f"DecisionEngine operator status error: {e}", exc_info=True)
            return {
                "request_id": raw_message.get("request_id"),
                "certificate_status": "error",
                "reason": str(e)
            }
