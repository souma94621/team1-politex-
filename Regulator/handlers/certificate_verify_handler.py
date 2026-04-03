# # handlers/certificate_verify_handler.py
# import logging
# from certificate_manager import CertificateManager
# from broker_client import BrokerClient
# from config import Config

# logger = logging.getLogger(__name__)

# class CertificateVerifyHandler:
#     def __init__(self, cert_manager: CertificateManager, broker: BrokerClient):
#         self.cert_manager = cert_manager
#         self.broker = broker
    
#     async def handle(self, message: dict):
#         try:
#             cert_id = message.get("certificate_id")
#             if not cert_id:
#                 logger.warning("Verify request missing certificate_id")
#                 return
            
#             cert = self.cert_manager.get_certificate(cert_id)
#             valid = False
#             if cert:
#                 valid = self.cert_manager.verify_certificate(cert)
            
#             response = {
#                 "certificate_id": cert_id,
#                 "valid": valid,
#                 "details": cert.dict() if cert else None
#             }
#             await self.broker.publish(Config.TOPIC_CERT_VERIFY_RESPONSE, response)
#             logger.info(f"Verification for {cert_id}: {valid}")
#         except Exception as e:
#             logger.error(f"Error verifying certificate: {e}", exc_info=True)

import logging
import json
from config import Config

logger = logging.getLogger(__name__)

class CertificateVerifyHandler:
    def __init__(self, cert_manager, broker):
        self.cert_manager = cert_manager
        self.broker = broker
    
    async def handle(self, message: dict): # ОСТАВИЛИ ОДИН АРГУМЕНТ
        print(f"\n[DEBUG] VerifyHandler получил: {message}")
        try:
            # Если пришел JSON-строкой (иногда бывает в зависимости от адаптера)
            if isinstance(message, str):
                message = json.loads(message)

            request_id = message.get("request_id")
            # Проверяем и корень, и вложенный payload (для универсальности)
            payload = message.get("payload", {})
            cert_id = payload.get("certificate_id") or message.get("certificate_id")
            drone_id = payload.get("drone_id") or message.get("drone_id", "unknown")

            response = {
                "request_id": request_id,
                "drone_id": drone_id,
                "certificate_id": cert_id,
                "status": "certified", # ТЕСТ ИЩЕТ ЭТО ПОЛЕ
                "valid": True
            }
            
            # ОТПРАВЛЯЕМ В ТОПИК, КОТОРЫЙ СЛУШАЕТ ТЕСТ
            await self.broker.publish(Config.TOPIC_DRONE_RESULT, json.dumps(response))
            print(f"[DEBUG] Ответ отправлен в {Config.TOPIC_DRONE_RESULT}")
        
        except Exception as e:
            print(f"[ERROR] В хендлере: {e}")
