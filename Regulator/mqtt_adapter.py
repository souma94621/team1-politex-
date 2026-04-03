import asyncio
import logging
import json
from typing import Callable, Dict, Any

from broker.mqtt.mqtt_system_bus import MQTTSystemBus

logger = logging.getLogger(__name__)

class MQTTBrokerAdapter:
    def __init__(self, broker: str = None, port: int = None, client_id: str = "regulator",
                 username: str = None, password: str = None, qos: int = 1):
        self.bus = MQTTSystemBus(
            broker=broker,
            port=port,
            client_id=client_id,
            qos=qos,
            username=username,
            password=password
        )
        self._loop = None
        self._running = False
        self._handlers: Dict[str, Callable] = {}

    async def connect(self):
        await asyncio.to_thread(self.bus.start)
        self._loop = asyncio.get_running_loop()
        self._running = True
        logger.info("MQTTSystemBus started")

    async def publish(self, topic: str, message: Any):
        if not self._running:
            raise RuntimeError("Bus not started")

        # MQTTSystemBus.publish ожидает dict — конвертируем строку если нужно
        if isinstance(message, str):
            message = json.loads(message)
        elif isinstance(message, bytes):
            message = json.loads(message.decode("utf-8"))

        success = await asyncio.to_thread(self.bus.publish, topic, message)
        return success

    async def subscribe(self, topic: str, handler: Callable):
        self._handlers[topic] = handler

        # MQTTSystemBus сам парсит JSON из байтов и вызывает callback(dict)
        # Поэтому callback принимает ОДИН аргумент — уже готовый dict
        def sync_callback(message: dict):
            if self._loop and self._running:
                try:
                    print(f"\n[MQTT DEBUG] Received on {topic}: {message}")
                    asyncio.run_coroutine_threadsafe(
                        handler(topic, message),
                        self._loop
                    )
                except Exception as e:
                    logger.error(f"Failed to process MQTT message: {e}")
            else:
                logger.warning("Event loop not available")

        await asyncio.to_thread(self.bus.subscribe, topic, sync_callback)
        logger.info(f"Subscribed to {topic}")

    async def start_consuming(self):
        logger.info("Consumers already running in background threads")

    async def close(self):
        if self._running:
            await asyncio.to_thread(self.bus.stop)
            self._running = False
            logger.info("MQTTSystemBus stopped")