"""
Точка входа регулятора.
Запуск: python -m src.regulator_component
"""
import asyncio
import json
import logging
import os
import signal
from pathlib import Path

from .src.config import Config
from .src.logger import setup_logging
from .src.broker_factory import create_broker_adapter
from .src.certificate_manager import CertificateManager
from .src.security_test_runner import SecurityTestRunner
from .src.coverage_controller import CoverageController
from .src.dispatcher import Dispatcher
from .src.security_goals_registry import SecurityGoalsRegistry
from .src.goals_check import GoalsCheck

from .src.handlers.firmware_handler import FirmwareHandler
from .src.handlers.drone_handler import DroneHandler
from .src.handlers.operator_handler import OperatorHandler
from .src.handlers.insurer_handler import InsurerHandler
from .src.handlers.certificate_verify_handler import CertificateVerifyHandler
from .src.handlers.certificate_revoke_handler import CertificateRevokeHandler

from .src.managers.ci_service import ContinuousIntegration
from .src.managers.decision_engine import DecisionEngine
from .src.managers.updater_service import UpdaterService

# Шаблон «Монитор» (ГОСТ Р 72118-2025, А.1)
from .src.monitor import SecurityMonitor


async def main():
    logger = setup_logging()
    logger.info("Starting Regulator Component...")

    # --- Пути и ключи ---
    current_dir = Path(__file__).parent
    private_key_path = os.getenv(
        "PRIVATE_KEY_PATH",
        str(current_dir / "src" / "keys" / "regulator_private.pem")
    )
    rules_path = current_dir / "src" / "monitor" / "security_knowledge_base.json"

    # Читаем версию из version.json
    version_file = current_dir / "version.json"
    current_version = "1.0.0"
    if version_file.exists():
        current_version = json.loads(version_file.read_text()).get("version", "1.0.0")

    # --- Инфраструктура ---
    cert_manager = CertificateManager(
        cert_storage_path=Config.CERT_STORAGE_PATH,
        crl_storage_path=Config.CRL_STORAGE_PATH,
        private_key=private_key_path,
    )

    goals_registry = SecurityGoalsRegistry(storage_path=Config.GOALS_STORAGE_PATH)
    goals_check = GoalsCheck(goals_registry)

    broker = create_broker_adapter()

    ci_service = ContinuousIntegration(
        goals_check=goals_check,
        signature_service_url=os.getenv("SIGNATURE_SERVICE_URL"),
        clone_timeout=int(os.getenv("CLONE_TIMEOUT", "60")),
        test_timeout=int(os.getenv("TEST_TIMEOUT", "300")),
    )

    test_runner = SecurityTestRunner(ci_service=ci_service)
    coverage_controller = CoverageController(mock=Config.MOCK_COVERAGE)

    # --- Хендлеры ---
    revoke_handler = CertificateRevokeHandler(cert_manager, broker)

    firmware_handler = FirmwareHandler(
        cert_manager, test_runner, coverage_controller,
        broker, goals_check, ci_service,
    )
    drone_handler    = DroneHandler(cert_manager, broker)
    operator_handler = OperatorHandler(cert_manager, broker)
    insurer_handler  = InsurerHandler(broker)
    verify_handler   = CertificateVerifyHandler(cert_manager, broker)

    # --- DecisionEngine (шаблон А.2) ---
    decision_engine = DecisionEngine(
        cert_manager=cert_manager,
        ci_service=ci_service,
        coverage_controller=coverage_controller,
        goals_check=goals_check,
    )

    # Обёртки для DecisionEngine
    async def firmware_via_engine(data):
        result = await decision_engine.decide_firmware_certification(data)
        await broker.publish(Config.TOPIC_FIRMWARE_RESULT, result)

    async def drone_via_engine(data):
        result = await decision_engine.decide_drone_registration(data)
        await broker.publish(Config.TOPIC_DRONE_RESULT, result)

    # --- Диспетчер ---
    dispatcher = Dispatcher()
    dispatcher.register(Config.TOPIC_FIRMWARE_REQUEST,       firmware_via_engine)
    dispatcher.register(Config.TOPIC_DRONE_REQUEST,          drone_via_engine)
    dispatcher.register(Config.TOPIC_OPERATOR_STATUS_REQUEST, operator_handler.handle)  # исправлено
    dispatcher.register(Config.TOPIC_INSURER_REQUEST,        insurer_handler.handle)
    dispatcher.register(Config.TOPIC_CERT_VERIFY_REQUEST,    verify_handler.handle)
    dispatcher.register(Config.TOPIC_CERT_REVOKE_REQUEST,    revoke_handler.handle)

    # --- Монитор безопасности (шаблон А.1) ---
    monitor = SecurityMonitor(
        broker_publish=broker.publish,
        rules_path=str(rules_path),
        revoke_handler=revoke_handler,
    )
    monitor.attach(dispatcher)   # датчик оборачивает dispatcher.dispatch()

    # --- Сервис обновлений (шаблон А.10) ---
    updater = UpdaterService(
        update_server_url=os.getenv("UPDATE_SERVER_URL", "https://updates.regulator.example"),
        public_key_path=os.getenv(
            "UPDATE_PUBLIC_KEY_PATH",
            str(current_dir / "src" / "keys" / "regulator_public_update.pem"),
        ),
        current_version=current_version,
        app_path=current_dir,
        check_interval_hours=int(os.getenv("UPDATE_CHECK_INTERVAL_HOURS", "24")),
    )

    # --- Graceful shutdown ---
    stop_event = asyncio.Event()

    def _on_signal(*_):
        logger.info("Shutdown signal received")
        stop_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, _on_signal)

    # --- Запуск ---
    try:
        await broker.connect()
        logger.info("Connected to broker")

        for topic in dispatcher.routes:
            await broker.subscribe(topic, dispatcher.dispatch)
            logger.info(f"Subscribed: {topic}")

        # Фоновые задачи
        asyncio.create_task(updater.start_auto_update_checker())

        logger.info("Regulator ready")
        await stop_event.wait()

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        logger.info("Shutting down...")
        await updater.close()
        await broker.close()
        logger.info("Regulator stopped")


if __name__ == "__main__":
    asyncio.run(main())