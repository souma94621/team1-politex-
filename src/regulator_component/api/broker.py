import asyncio
import json
from broker_client import BrokerClient


class BrokerService:
    def __init__(self):
        self.broker = BrokerClient()

    async def send_and_wait(self, request_topic, response_topic, payload):
        response = None

        async def handler(message):
            nonlocal response
            if isinstance(message, (bytes, str)):
                response = json.loads(message)
            else:
                response = message

        await self.broker.subscribe(response_topic, handler)
        await self.broker.publish(request_topic, payload)

        # ждём ответ
        for _ in range(20):
            if response:
                return response
            await asyncio.sleep(0.5)

        return {"error": "timeout"}