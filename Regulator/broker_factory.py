import logging
from config import Config
from kafka_adapter import KafkaBrokerAdapter
from mqtt_adapter import MQTTBrokerAdapter

logger = logging.getLogger(__name__)

def create_broker_adapter():
    broker_type = Config.BROKER_TYPE.lower()
    if broker_type == "kafka":
        logger.info("Creating Kafka broker adapter")
        return KafkaBrokerAdapter(
            bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
            client_id=Config.KAFKA_CLIENT_ID,
            group_id=Config.KAFKA_GROUP_ID,
            username=Config.KAFKA_USERNAME,
            password=Config.KAFKA_PASSWORD
        )
    elif broker_type == "mqtt":
        logger.info("Creating MQTT broker adapter")
        return MQTTBrokerAdapter(
            broker=Config.MQTT_BROKER,
            port=Config.MQTT_PORT,
            client_id=Config.MQTT_CLIENT_ID,
            username=Config.MQTT_USERNAME,
            password=Config.MQTT_PASSWORD,
            qos=Config.MQTT_QOS
        )
    else:
        raise ValueError(f"Unknown BROKER_TYPE: {Config.BROKER_TYPE}")