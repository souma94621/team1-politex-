import asyncio
import sys
import os
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

# Импорт обработчиков
from handlers.firmware_handler import FirmwareHandler
from handlers.drone_handler import DroneHandler
from handlers.operator_handler import OperatorHandler
from handlers.insurer_handler import InsurerHandler
from handlers.certificate_verify_handler import CertificateVerifyHandler
from handlers.certificate_revoke_handler import CertificateRevokeHandler

async def main():
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
    
    # 3. Создание адаптера брокера
    broker = create_broker_adapter()

    # 4. Регистрация обработчиков бизнес-логики
    firmware_handler = FirmwareHandler(cert_manager, test_runner, coverage_controller, broker)
    drone_handler = DroneHandler(cert_manager, broker)
    operator_handler = OperatorHandler(cert_manager, broker)
    insurer_handler = InsurerHandler(broker)
    verify_handler = CertificateVerifyHandler(cert_manager, broker)
    revoke_handler = CertificateRevokeHandler(cert_manager, broker)
    
    # 5. Настройка Диспетчера
    dispatcher = Dispatcher()
    
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

    # 6. Запуск сетевого взаимодействия
    try:
        logger.info("Connecting to broker...")
        await broker.connect()
        
        # Подписка: используем safe_dispatch вместо dispatcher.dispatch
        for topic in dispatcher.routes.keys():
            await broker.subscribe(topic, safe_dispatch) # <-- ЗАМЕНИЛИ ЗДЕСЬ
            logger.info(f"Subscribed to topic: {topic}")
        
        logger.info("Regulator is ready and consuming messages.")
        await broker.start_consuming()
        
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Manual shutdown initiated...")
    except Exception as e:
        logger.error(f"Critical system error: {e}")
    finally:
        logger.info("Closing connections...")
        await broker.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
