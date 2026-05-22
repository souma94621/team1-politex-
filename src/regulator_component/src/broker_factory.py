import logging
from .config import Config
from .broker_client import BrokerClient

logger = logging.getLogger(__name__)


def create_broker_adapter() -> BrokerClient:
    logger.info(f"Creating BrokerClient (type={Config.BROKER_TYPE}, url={Config.BROKER_URL})")
    return BrokerClient(
        url=Config.BROKER_URL,
        exchange=Config.EXCHANGE_NAME
    )