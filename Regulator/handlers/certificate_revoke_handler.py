# handlers/certificate_revoke_handler.py
import logging
from certificate_manager import CertificateManager
from broker.src.system_bus import SystemBus
from config import Config

logger = logging.getLogger(__name__)

class CertificateRevokeHandler:
    def def __init__(self, cert_manager: CertificateManager, bus: SystemBus):
        self.cert_manager = cert_manager
        self.bus = bus
    
    async def handle(self, message: dict):
        payload = message.get("payload", {})
        cert_id = payload.get("certificate_id")
        reason = payload.get("reason", "")

        self.cert_manager.revoke_certificate(cert_id)

        self.bus.respond(message, {
            "certificate_id": cert_id,
            "revoked": True,
            "reason": reason
        }
        self.bus.respond(message, response)
        await self.broker.publish(Config.TOPIC_CERT_REVOKE_RESPONSE, response)
            logger.info(f"Revoked certificate {cert_id}")
        except Exception as e:
            logger.error(f"Error revoking certificate: {e}", exc_info=True)
        )
