# broker_client.py
import asyncio
import json
import logging
from typing import Callable, Dict, Any

logger = logging.getLogger(__name__)

class BrokerClient:
    def __init__(self, url: str, exchange: str):
        self.url = url
        self.exchange = exchange
        self.handlers: Dict[str, Callable] = {}
    
    async def connect(self):
        # В реальности здесь подключение к RabbitMQ/Kafka
        logger.info(f"Connecting to broker at {self.url}")
        # Имитируем успешное подключение
        await asyncio.sleep(0.1)
    
    async def publish(self, topic: str, message: Dict[str, Any]):
        # Сериализация и публикация
        logger.info(f"Publishing to {topic}: {json.dumps(message)}")
        # В реальности отправка в брокер
        await asyncio.sleep(0.01)
    
    async def subscribe(self, topic: str, handler: Callable):
        self.handlers[topic] = handler
        logger.info(f"Subscribed to {topic}")
        # В реальности запускаем потребление
    
    async def start_consuming(self):
        # Эмуляция получения сообщений: для тестов можно запустить фоновую задачу,
        # но в этом примере мы не эмулируем входящие сообщения автоматически.
        # Для интеграционных тестов можно использовать отдельный механизм.
        logger.info("Broker client started (emulation mode). No automatic message injection.")