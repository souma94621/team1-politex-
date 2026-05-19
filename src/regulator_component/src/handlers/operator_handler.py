# handlers/operator_handler.py
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from ..certificate_manager import CertificateManager
from ..broker_client import BrokerClient
from ..config import Config
from ..models import Certificate

logger = logging.getLogger(__name__)


class OperatorHandler:
    """
    Обработчик запросов от эксплуатантов на проверку статуса сертификата дрона.
    Возвращает расширенную информацию о сертификате дрона и его прошивке.
    """

    def __init__(self, cert_manager: CertificateManager, broker: BrokerClient):
        self.cert_manager = cert_manager
        self.broker = broker

    async def handle(self, message: Dict[str, Any]):
        try:
            operator_id = message.get("operator_id")
            drone_id = message.get("drone_id")
            request_id = message.get("request_id")

            if not operator_id or not drone_id:
                logger.warning("OperatorHandler: missing operator_id or drone_id")
                await self._publish_error_response(request_id, "Missing operator_id or drone_id")
                return

            logger.info(f"Operator {operator_id} requested certificate status for drone {drone_id}")

            # 1. Найти действующий сертификат дрона
            drone_cert = self.cert_manager.find_certificate_by_subject("drone", drone_id)
            if not drone_cert:
                await self._publish_response(
                    request_id=request_id,
                    operator_id=operator_id,
                    drone_id=drone_id,
                    is_valid=False,
                    reason="Drone not found or has no active certificate"
                )
                return

            # 2. Полная проверка сертификата дрона
            is_cert_valid = self.cert_manager.verify_certificate(drone_cert)
            if not is_cert_valid:
                await self._publish_response(
                    request_id=request_id,
                    operator_id=operator_id,
                    drone_id=drone_id,
                    is_valid=False,
                    reason="Certificate is revoked, expired, or has invalid signature",
                    certificate_details=self._extract_certificate_info(drone_cert)
                )
                return

            # 3. Если сертификат дрона валиден, найти информацию о его прошивке
            firmware_cert_id = None
            if drone_cert.extra:
                firmware_cert_id = drone_cert.extra.get("firmware_certificate_id")
            
            firmware_info = None
            if firmware_cert_id:
                firmware_cert = self.cert_manager.get_certificate(firmware_cert_id)
                if firmware_cert:
                    firmware_info = self._extract_certificate_info(firmware_cert)

            # 4. Собрать расширенный ответ
            await self._publish_response(
                request_id=request_id,
                operator_id=operator_id,
                drone_id=drone_id,
                is_valid=True,
                reason=None,
                certificate_details=self._extract_certificate_info(drone_cert),
                firmware_details=firmware_info,
                owner_id=drone_cert.owner_id
            )

        except Exception as e:
            logger.error(f"OperatorHandler error: {e}", exc_info=True)
            await self._publish_error_response(message.get("request_id"), str(e))

    def _extract_certificate_info(self, cert: Certificate) -> Dict[str, Any]:
        """Извлекает основную информацию из сертификата."""
        return {
            "certificate_id": cert.certificate_id,
            "subject_type": cert.subject_type,
            "subject_id": cert.subject_id,
            "issued_at": cert.issued_at.isoformat(),
            "valid_until": cert.valid_until.isoformat(),
            "security_goals": cert.security_goals,
            "digital_signature": cert.digital_signature[:16] + "..." if cert.digital_signature else None,
        }

    async def _publish_response(
        self,
        request_id: Optional[str],
        operator_id: str,
        drone_id: str,
        is_valid: bool,
        reason: Optional[str],
        certificate_details: Optional[Dict[str, Any]] = None,
        firmware_details: Optional[Dict[str, Any]] = None,
        owner_id: Optional[str] = None
    ):
        """Публикует расширенный ответ о статусе сертификата дрона."""
        response = {
            "request_id": request_id,
            "operator_id": operator_id,
            "drone_id": drone_id,
            "timestamp": datetime.utcnow().isoformat(),
            "certificate_status": "valid" if is_valid else "invalid",
            "reason": reason,
            "drone_certificate": certificate_details,
            "firmware_certificate": firmware_details,
            "owner_id": owner_id,
        }
        await self.broker.publish(Config.TOPIC_OPERATOR_RESULT, response)
        logger.info(f"Published certificate status for drone {drone_id} to operator {operator_id}: {response['certificate_status']}")

    async def _publish_error_response(self, request_id: Optional[str], error_message: str):
        """Публикует ответ об ошибке."""
        response = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "certificate_status": "error",
            "reason": error_message,
        }
        await self.broker.publish(Config.TOPIC_OPERATOR_RESULT, response)
