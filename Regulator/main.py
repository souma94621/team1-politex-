import asyncio
import sys
import os
import logging
import json  # <-- ДОБАВИЛИ ИМПОРТ JSON
from pathlib import Path

# Подгружаем переменные окружения (.env)
from dotenv import load_dotenv
load_dotenv()

from config import Config
from logger import setup_logging
from broker_factory import create_broker_adapter
from certificate_manager import CertificateManager
from security_test_runner import SecurityTestRunner
from coverage_controller import CoverageController
from dispatcher import Dispatcher
from broker.bus_factory import create_system_bus

# Импорт обработчиков
from handlers.firmware_handler import FirmwareHandler
from handlers.drone_handler import DroneHandler
from handlers.operator_handler import OperatorHandler
from handlers.insurer_handler import InsurerHandler
from handlers.certificate_verify_handler import CertificateVerifyHandler
from handlers.certificate_revoke_handler import CertificateRevokeHandler
from certificate_manager import CertificateManager
logger = logging.getLogger(__name__)

async def main():
    bus = create_system_bus(client_id="regulator")
    bus.start()
    # 1. Настройка логирования
    logger = setup_logging()
    logger.info("Starting Regulator System...")

    # 2. Инициализация ключевых компонентов безопасности
    private_key = os.getenv("PRIVATE_KEY", "dummy_private_key_for_testing")
    
    cert_manager = CertificateManager(
        cert_storage_path=Config.CERT_STORAGE_PATH,
        crl_storage_path=Config.CRL_STORAGE_PATH,
        private_key=private_key
    )
    
    test_runner = SecurityTestRunner(mock=Config.MOCK_SECURITY_TESTS)
    coverage_controller = CoverageController(mock=Config.MOCK_COVERAGE)
    

    # Регистрация обработчиков бизнес-логики
    firmware_handler = FirmwareHandler(cert_manager, test_runner, coverage_controller, broker)
    drone_handler = DroneHandler(cert_manager, bus)
    operator_handler = OperatorHandler(cert_manager, bus)
    insurer_handler = InsurerHandler(bus)
    verify_handler = CertificateVerifyHandler(cert_manager, bus)
    revoke_handler = CertificateRevokeHandler(cert_manager, bus)
    
    # 5. Настройка Диспетчера
    def sync_dispatch(message):
    asyncio.run_coroutine_threadsafe(
        dispatcher.dispatch(message),
        loop
    )

    bus.subscribe("systems.certification", sync_dispatch)
    
    routes = {
        Config.TOPIC_FIRMWARE_REQUEST: firmware_handler.handle,
        Config.TOPIC_DRONE_REQUEST: drone_handler.handle,
        Config.TOPIC_OPERATOR_REQUEST: operator_handler.handle,
        Config.TOPIC_INSURER_REQUEST: insurer_handler.handle,
        Config.TOPIC_CERT_VERIFY_REQUEST: verify_handler.handle,
        Config.TOPIC_CERT_REVOKE_REQUEST: revoke_handler.handle,
    }

    for topic, handler_func in routes.items():
        dispatcher.register(topic, handler_func)
        logger.info(f"Registered route: {topic}")

    # --- НОВАЯ ФУНКЦИЯ ДЛЯ ИСПРАВЛЕНИЯ ОШИБКИ ---
    async def safe_dispatch(topic, data):
        # data уже должен быть словарем благодаря правке в адаптере выше
        await dispatcher.dispatch(topic, data)

    loop = asyncio.get_event_loop()
    
    #  SystemBus вместо broker
    bus = create_system_bus(client_id="regulator")
    bus.start()

    cert_manager = CertificateManager()
    dispatcher = Dispatcher()

    # handlers
    verify_handler = CertificateVerifyHandler(cert_manager, bus)
    revoke_handler = CertificateRevokeHandler(cert_manager, bus)

    # регистрация action
    dispatcher.register("verify_certificate", verify_handler.handle)
    dispatcher.register("revoke_certificate", revoke_handler.handle)

    #  bridge sync → async
    def safe_dispatch(message):
        asyncio.run_coroutine_threadsafe(
            dispatcher.dispatch(message),
            loop
        )

    #  подписка (ОДИН ТОПИК!)
    bus.subscribe("systems.certification", safe_dispatch)

    logger.info("Regulator started with SystemBus 🚀")

    # просто держим приложение живым
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
