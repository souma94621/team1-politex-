# handlers/firmware_handler.py
import logging
import json
from datetime import datetime
from models import FirmwareRequest, FirmwareResult
from certificate_manager import CertificateManager
from security_test_runner import SecurityTestRunner
from coverage_controller import CoverageController
from broker_client import BrokerClient
from config import Config

# Настройка логирования для этого модуля
logger = logging.getLogger(__name__)

class FirmwareHandler:
    def __init__(self, cert_manager: CertificateManager, test_runner: SecurityTestRunner,
                 coverage_controller: CoverageController, broker: BrokerClient):
        self.cert_manager = cert_manager
        self.test_runner = test_runner
        self.coverage_controller = coverage_controller
        self.broker = broker
    
    async def handle(self, message):
        """
        Основной метод обработки запроса на сертификацию прошивки.
        """
        try:
            # 1. Десериализация (на случай, если в main.py пришла строка)
            if isinstance(message, (str, bytes)):
                data = json.loads(message)
            else:
                data = message

            # ← ДОБАВЬ ЭТИ ДВЕ СТРОКИ ВРЕМЕННО
            logger.info(f"[DEBUG] type(data) = {type(data)}")
            logger.info(f"[DEBUG] data = {data}")


            # Превращаем словарь в Pydantic-модель
            req = FirmwareRequest(**data)
            logger.info(f"--- [START] Processing firmware request: {req.request_id} ---")
            
            # 2. Запуск тестов безопасности (Cyberimmune-дизайн)
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
                # Публикуем как JSON строку
                await self.broker.publish(Config.TOPIC_FIRMWARE_RESULT, result.model_dump_json())
                return
            
            # 3. Создание сертификата (если тесты пройдены)
            logger.info(f"Security tests passed. Generating certificate...")
            cert = self.cert_manager.create_certificate(
                subject_type="firmware",
                subject_id=req.firmware.get("commit_hash", req.request_id),
                security_goals=["FW-SEC-01", "FW-SEC-02", "FW-SEC-05"]
            )
            
            # 4. Формирование финального результата
            result = FirmwareResult(
                request_id=req.request_id,
                timestamp=datetime.now(),
                status="CERTIFIED",
                certificate=cert.model_dump() # Превращаем сертификат в словарь для Pydantic
            )

            # 5. ОТПРАВКА ОТВЕТА (Критически важный момент)
            # Превращаем всю модель результата в JSON-строку
            response_json = result.model_dump_json()
            
            await self.broker.publish(Config.TOPIC_FIRMWARE_RESULT, response_json)
            logger.info(f"+++ [SUCCESS] Firmware {req.request_id} certified as {cert.certificate_id} +++")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON message: {e}")
        except Exception as e:
            logger.error(f"Error in FirmwareHandler: {e}", exc_info=True)