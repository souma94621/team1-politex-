# kafka_adapter.py
import asyncio
import json
import logging
from typing import Callable, Dict, Any, Optional

from broker.kafka.kafka_system_bus import KafkaSystemBus

logger = logging.getLogger(__name__)

class KafkaBrokerAdapter:
    """
    Адаптер для KafkaSystemBus, предоставляющий асинхронный интерфейс,
    аналогичный BrokerClient.
    """
    def __init__(self, bootstrap_servers: str, client_id: str = "regulator",
                 group_id: str = None, username: str = None, password: str = None):
        self.bus = KafkaSystemBus(
            bootstrap_servers=bootstrap_servers,
            client_id=client_id,
            group_id=group_id,
            username=username,
            password=password
        )
        self._loop = None
        self._running = False
        self._handlers: Dict[str, Callable] = {}

    async def connect(self):
        """Запускает bus (синхронно, но в отдельном потоке)."""
        await asyncio.to_thread(self.bus.start)
        self._loop = asyncio.get_running_loop()
        self._running = True
        logger.info("KafkaSystemBus started")

    async def publish(self, topic: str, message: Dict[str, Any]):
        """Асинхронная публикация."""
        if not self._running:
            raise RuntimeError("Bus not started")
        # Публикация синхронная, но может блокировать, поэтому выносим в поток
        success = await asyncio.to_thread(self.bus.publish, topic, message)
        if not success:
            logger.error(f"Failed to publish to {topic}")
        return success

    async def subscribe(self, topic: str, handler: Callable):
        """
        Подписывается на топик, handler – асинхронная функция.
        """
        self._handlers[topic] = handler

        def sync_callback(message: Dict[str, Any]):
            # Этот callback вызывается из потока потребителя KafkaSystemBus
            # Нужно вызвать асинхронный handler в главном event loop
            if self._loop and self._running:
                asyncio.run_coroutine_threadsafe(handler(topic, message), self._loop)
            else:
                logger.warning("Event loop not available, dropping message")

        # Подписываемся синхронно
        await asyncio.to_thread(self.bus.subscribe, topic, sync_callback)
        logger.info(f"Subscribed to {topic}")

    async def start_consuming(self):
        """
        В KafkaSystemBus потребление уже запущено в потоках через bus.start().
        Здесь просто ждём, пока приложение работает.
        """
        # Потоки уже запущены, просто держим флаг
        logger.info("Consumers already running in background threads")
        # Можно добавить ожидание завершения, но это будет в main через asyncio.Event

    async def close(self):
        """Останавливает bus."""
        if self._running:
            await asyncio.to_thread(self.bus.stop)
            self._running = False
            logger.info("KafkaSystemBus stopped")