import asyncio
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
from .src.security_goals_registry import SecurityGoalsRegistry   # NEW

from .src.handlers.firmware_handler import FirmwareHandler
from .src.handlers.drone_handler import DroneHandler
from .src.handlers.operator_handler import OperatorHandler
from .src.handlers.insurer_handler import InsurerHandler
from .src.handlers.certificate_verify_handler import CertificateVerifyHandler
from .src.handlers.certificate_revoke_handler import CertificateRevokeHandler

# NEW: импорт новых хендлеров
from .src.handlers.system_cert_handler import SystemCertHandler
from .src.handlers.owner_transfer_handler import OwnerTransferHandler
from .src.handlers.operator_certificate_status_handler import OperatorCertificateStatusHandler

from .src.security_goals_registry import SecurityGoalsRegistry   # NEW
from .src.goals_check import GoalsCheck                         # NEW

from .src.managers.ci_service import ContinuousIntegration
from .src.security_test_runner import SecurityTestRunner

from .src.managers.updater_service import UpdaterService

from .src.managers.decision_engine import DecisionEngine

async def main():
    # ... (инициализация cert_manager, test_runner и т.д.)


    # NEW: создаём DecisionEngine
    decision_engine = DecisionEngine(
        cert_manager=cert_manager,
        ci_service=ci_service,
        coverage_controller=coverage_controller,
        goals_check=goals_check
    )

    # NEW: функции-обёртки для DecisionEngine (вместо старых хендлеров)
    async def firmware_dispatcher(data):
        result = await decision_engine.decide_firmware_certification(data)
        await broker.publish(Config.TOPIC_FIRMWARE_RESULT, result)

    async def drone_dispatcher(data):
        result = await decision_engine.decide_drone_registration(data)
        await broker.publish(Config.TOPIC_DRONE_RESULT, result)

    async def operator_dispatcher(data):
        result = await decision_engine.decide_operator_status(data)
        await broker.publish(Config.TOPIC_OPERATOR_RESULT, result)

    async def system_dispatcher(data):
        result = await decision_engine.decide_system_certification(data)
        await broker.publish(Config.TOPIC_SYSTEM_CERT_RESPONSE, result)

    async def transfer_dispatcher(data):
        result = await decision_engine.decide_owner_transfer(data)
        await broker.publish(Config.TOPIC_DRONE_TRANSFER_RESPONSE, result)

    # Создаём диспетчер и регистрируем новые обёртки
    dispatcher = Dispatcher()
    
    dispatcher.register(Config.TOPIC_FIRMWARE_REQUEST, firmware_dispatcher)
    dispatcher.register(Config.TOPIC_DRONE_REQUEST, drone_dispatcher)
    dispatcher.register(Config.TOPIC_OPERATOR_REQUEST, operator_dispatcher)
    dispatcher.register(Config.TOPIC_SYSTEM_CERT_REQUEST, system_dispatcher)
    dispatcher.register(Config.TOPIC_DRONE_TRANSFER_REQUEST, transfer_dispatcher)
    
    # Остальные топики (страховка, проверка, отзыв) можно оставить на старых хендлерах
    # или тоже перевести на DecisionEngine, если у них есть методы
    dispatcher.register(Config.TOPIC_INSURER_REQUEST, insurer_handler.handle)
    dispatcher.register(Config.TOPIC_CERT_VERIFY_REQUEST, verify_handler.handle)
    dispatcher.register(Config.TOPIC_CERT_REVOKE_REQUEST, revoke_handler.handle)

    # ... дальше как обычно
    for topic in dispatcher.routes.keys():
        await broker.subscribe(topic, dispatcher.dispatch)
    # NEW: создаём реестр целей и GoalsCheck
    goals_registry = SecurityGoalsRegistry()
    goals_check = GoalsCheck(goals_registry)

    # ... создаём брокер

    # Передаём goals_check во все хендлеры, которым он нужен
    firmware_handler = FirmwareHandler(
        cert_manager, test_runner, coverage_controller, broker,
        goals_check=goals_check          # NEW
    )
    drone_handler = DroneHandler(cert_manager, broker)   # пока не использует, но можно добавить позже
    operator_handler = OperatorHandler(cert_manager, broker)
    insurer_handler = InsurerHandler(broker)
    verify_handler = CertificateVerifyHandler(cert_manager, broker)
    revoke_handler = CertificateRevokeHandler(cert_manager, broker)

    # NEW: SystemCertHandler с goals_check
    system_cert_handler = SystemCertHandler(cert_manager, broker, goals_check)
    owner_transfer_handler = OwnerTransferHandler(cert_manager, broker)
    operator_status_handler = OperatorCertificateStatusHandler(cert_manager, broker)

    # ... регистрация маршрутов и запуск
    logger = setup_logging()
    logger.info("Starting Regulator System (Component Mode)...")

    current_dir = Path(__file__).parent
    default_key_path = current_dir / "src" / "keys" / "regulator_private.pem"
    private_key = os.getenv("PRIVATE_KEY", str(default_key_path))

    cert_manager = CertificateManager(
        cert_storage_path=Config.CERT_STORAGE_PATH,
        crl_storage_path=Config.CRL_STORAGE_PATH,
        private_key=private_key
    )

    test_runner = SecurityTestRunner(mock=Config.MOCK_SECURITY_TESTS)
    coverage_controller = CoverageController(mock=Config.MOCK_COVERAGE)

    # NEW: инициализация реестра целей безопасности
    goals_registry = SecurityGoalsRegistry()

    broker = create_broker_adapter()

    # Существующие хендлеры
    firmware_handler = FirmwareHandler(cert_manager, test_runner, coverage_controller, broker)
    drone_handler = DroneHandler(cert_manager, broker)
    operator_handler = OperatorHandler(cert_manager, broker)
    insurer_handler = InsurerHandler(broker)
    verify_handler = CertificateVerifyHandler(cert_manager, broker)
    revoke_handler = CertificateRevokeHandler(cert_manager, broker)

    # NEW: создание новых хендлеров
    system_cert_handler = SystemCertHandler(cert_manager, broker, goals_registry)
    owner_transfer_handler = OwnerTransferHandler(cert_manager, broker)
    operator_status_handler = OperatorCertificateStatusHandler(cert_manager, broker)

    dispatcher = Dispatcher()

    # Инициализация GoalsCheck и CI
    goals_registry = SecurityGoalsRegistry()
    goals_check = GoalsCheck(goals_registry)

    ci_service = ContinuousIntegration(
        goals_check=goals_check,
        signature_service_url=os.getenv("SIGNATURE_SERVICE_URL"),
        clone_timeout=int(os.getenv("CLONE_TIMEOUT", "60")),
        test_timeout=int(os.getenv("TEST_TIMEOUT", "300"))
    )

    # Обновляем тест-раннер (не мок)
    test_runner = SecurityTestRunner(ci_service=ci_service)  # больше не используем mock

    # coverage_controller можно оставить с mock или сделать реальный
    coverage_controller = CoverageController(mock=Config.MOCK_COVERAGE)

    # Передаём ci_service в firmware_handler
    firmware_handler = FirmwareHandler(
        cert_manager,
        test_runner,
        coverage_controller,
        broker,
        goals_check,
        ci_service      # NEW
    )

# Инициализация сервиса обновлений
update_server_url = os.getenv("UPDATE_SERVER_URL", "https://updates.regulator.example")
public_key_path = os.getenv("UPDATE_PUBLIC_KEY_PATH", "src/keys/regulator_public_update.pem")
current_version = "1.0.0"  # или читаем из version.json

# Определяем путь к приложению (корень регулятора)
app_path = Path(__file__).parent.parent  # или Path.cwd()

updater = UpdaterService(
    update_server_url=update_server_url,
    public_key_path=public_key_path,
    current_version=current_version,
    app_path=app_path,
    check_interval_hours=int(os.getenv("UPDATE_CHECK_INTERVAL_HOURS", "24"))
)

 # Запускаем фоновую проверку обновлений
 asyncio.create_task(updater.start_auto_update_checker())

# Обработка сигналов для graceful shutdown
def shutdown_handler():
    asyncio.create_task(updater.close())

signal.signal(signal.SIGTERM, lambda *_: shutdown_handler())
signal.signal(signal.SIGINT, lambda *_: shutdown_handler())
    routes = {
        Config.TOPIC_FIRMWARE_REQUEST:       firmware_handler.handle,
        Config.TOPIC_DRONE_REQUEST:          drone_handler.handle,
        Config.TOPIC_OPERATOR_REQUEST:       operator_handler.handle,
        Config.TOPIC_INSURER_REQUEST:        insurer_handler.handle,
        Config.TOPIC_CERT_VERIFY_REQUEST:    verify_handler.handle,
        Config.TOPIC_CERT_REVOKE_REQUEST:    revoke_handler.handle,
        # NEW: новые маршруты
        Config.TOPIC_SYSTEM_CERT_REQUEST:    system_cert_handler.handle,
        Config.TOPIC_DRONE_TRANSFER_REQUEST: owner_transfer_handler.handle,
        Config.TOPIC_OPERATOR_STATUS_REQUEST: operator_status_handler.handle,
    }

    for topic, handler_func in routes.items():
        dispatcher.register(topic, handler_func)
        logger.info(f"Registered route: {topic}")

    async def safe_dispatch(topic, data):
        await dispatcher.dispatch(topic, data)

    try:
        logger.info("Connecting to broker...")
        await broker.connect()

        for topic in dispatcher.routes.keys():
            await broker.subscribe(topic, safe_dispatch)
            logger.info(f"Subscribed to topic: {topic}")

        logger.info("Regulator Component is ready and consuming messages.")
        await broker.start_consuming()

        while True:
            await asyncio.sleep(1)

    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Shutdown initiated...")
    except Exception as e:
        logger.error(f"Critical system error: {e}")
    finally:
        logger.info("Closing connections...")
        await broker.close()
        logger.info("Regulator stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
        
