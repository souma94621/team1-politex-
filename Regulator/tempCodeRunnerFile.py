# main.py (изменённый)
import asyncio
import sys
from pathlib import Path

from config import Config
from logger import setup_logging
from broker_factory import create_broker_adapter
from certificate_manager import CertificateManager
from security_test_runner import SecurityTestRunner
from coverage_controller import CoverageController
from dispatcher import Dispatcher
from handlers.firmware_handler import FirmwareHandler
from handlers.drone_handler import DroneHandler
from handlers.operator_handler import OperatorHandler
from handlers.insurer_handler import InsurerHandler
from handlers.certificate_verify_handler import CertificateVerifyHandler
from handlers.certificate_revoke_handler import CertificateRevokeHandler

logger = None   # будет инициализирован в setup_logging

async def main():
    global logger
    logger = setup_logging()   # предполагается, что setup_logging возвращает logger
    logger.info("Starting Regulator with Kafka broker")
    
    # Инициализация компонентов
    private_key = "dummy_private_key_for_testing"
    cert_manager = CertificateManager(
        cert_storage_path=Config.CERT_STORAGE_PATH,
        crl_storage_path=Config.CRL_STORAGE_PATH,
        private_key=private_key
    )
    test_runner = SecurityTestRunner(mock=Config.MOCK_SECURITY_TESTS)
    coverage_controller = CoverageController(mock=Config.MOCK_COVERAGE)
    # ... инициализация ...
    broker = create_broker_adapter()

    # Обработчики
    firmware_handler = FirmwareHandler(cert_manager, test_runner, coverage_controller, broker)
    drone_handler = DroneHandler(cert_manager, broker)
    operator_handler = OperatorHandler(cert_manager, broker)
    insurer_handler = InsurerHandler(broker)
    verify_handler = CertificateVerifyHandler(cert_manager, broker)
    revoke_handler = CertificateRevokeHandler(cert_manager, broker)
    
    # Диспетчер
    dispatcher = Dispatcher()
    dispatcher.register(Config.TOPIC_FIRMWARE_REQUEST, firmware_handler.handle)
    dispatcher.register(Config.TOPIC_DRONE_REQUEST, drone_handler.handle)
    dispatcher.register(Config.TOPIC_OPERATOR_REQUEST, operator_handler.handle)
    dispatcher.register(Config.TOPIC_INSURER_REQUEST, insurer_handler.handle)
    dispatcher.register(Config.TOPIC_CERT_VERIFY_REQUEST, verify_handler.handle)
    dispatcher.register(Config.TOPIC_CERT_REVOKE_REQUEST, revoke_handler.handle)
    
    # Подключение к брокеру и подписка
    await broker.connect()
    for topic in dispatcher.routes.keys():
        # Здесь подписываемся, передавая обработчик, который принимает (topic, message)
        await broker.subscribe(topic, dispatcher.dispatch)
    
    # Запуск потребления (фактически уже запущено, но держим флаг)
    await broker.start_consuming()
    
    # Держим приложение запущенным
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await broker.close()

if __name__ == "__main__":
    asyncio.run(main())