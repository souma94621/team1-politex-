import asyncio
import logging

from broker_factory import create_broker_adapter
from dispatcher import Dispatcher
from config import Config

from certificate_manager import CertificateManager
from security_test_runner import SecurityTestRunner
from coverage_controller import CoverageController
from goals_check import GoalsCheck
from cryptography.hazmat.primitives import serialization
from goals_check import GoalsCheck
from security_goals_registry import SecurityGoalsRegistry

from managers.ci_service import ContinuousIntegration

from handlers.firmware_handler import FirmwareHandler
from handlers.drone_handler import DroneHandler
from handlers.insurer_handler import InsurerHandler
from handlers.certificate_verify_handler import CertificateVerifyHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting regulator runtime...")

    broker = create_broker_adapter()

    await broker.connect()

    dispatcher = Dispatcher()

    with open(Config.PRIVATE_KEY_PATH, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None
        )

    cert_manager = CertificateManager(
        cert_storage_path=Config.CERT_STORAGE_PATH,
        crl_storage_path=Config.CRL_STORAGE_PATH,
        private_key=private_key
    )
    

    registry_service = SecurityGoalsRegistry()

    goals_checker = GoalsCheck(registry=registry_service)

    ci_service = ContinuousIntegration(goals_check=goals_checker)

    test_runner = SecurityTestRunner(
        ci_service=ci_service
    )

    coverage_controller = CoverageController()

    firmware_handler = FirmwareHandler(
        cert_manager=cert_manager,
        test_runner=test_runner,
        coverage_controller=coverage_controller,
        broker=broker,
        goals_check=goals_checker,
        ci_service=ci_service
    )

    drone_handler = DroneHandler(
        cert_manager=cert_manager,
        broker=broker
    )

    insurer_handler = InsurerHandler(
        broker=broker
    )

    verify_handler = CertificateVerifyHandler(
        cert_manager=cert_manager,
        broker=broker
    )

    dispatcher.register(
        Config.TOPIC_FIRMWARE_REQUEST,
        firmware_handler.handle
    )

    dispatcher.register(
    Config.TOPIC_DRONE_REQUEST,
    drone_handler.handle
    )

    dispatcher.register(
        Config.TOPIC_INSURER_REQUEST,
        insurer_handler.handle
    )

    dispatcher.register(
        Config.TOPIC_CERT_VERIFY_REQUEST,
        verify_handler.handle
    )

    async def wrapped_handler(topic, message):
        await dispatcher.dispatch(topic, message)

    await broker.subscribe(
        Config.TOPIC_FIRMWARE_REQUEST,
        wrapped_handler
    )

    await broker.subscribe(
    Config.TOPIC_DRONE_REQUEST,
    wrapped_handler
    )

    await broker.subscribe(
        Config.TOPIC_INSURER_REQUEST,
        wrapped_handler
    )

    await broker.subscribe(
        Config.TOPIC_CERT_VERIFY_REQUEST,
        wrapped_handler
    )

    logger.info("Runtime ready")

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())