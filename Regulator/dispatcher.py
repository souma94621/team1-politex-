import json
import logging

logger = logging.getLogger(__name__)

class Dispatcher:
    def __init__(self):
        self.routes = {}

    def register(self, action, handler):
        self.routes[action] = handler

    async def dispatch(self, message):
        try:
            # 1. Декодируем сообщение
            if isinstance(message, str):
                data = json.loads(message)
            elif isinstance(message, bytes):
                data = json.loads(message.decode())
            else:
                data = message

            # 2. Берём action
            action = data.get("action")

            if not action:
                logger.warning("Message without action")
                return

            # 3. Ищем handler
            handler = self.routes.get(action)

            if not handler:
                logger.warning(f"No handler for action: {action}")
                return

            # 4. Вызываем handler
            await handler(data)

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON: {message}")
        except Exception as e:
            logger.error(f"Error in dispatcher: {e}", exc_info=True)
