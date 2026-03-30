import asyncio
import logging
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# 1. Добавляем текущую папку в пути, чтобы Python видел models и прочее
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# 2. Импортируем классы напрямую
try:
    from handlers.firmware_handler import FirmwareHandler
    from certificate_manager import CertificateManager
except ImportError as e:
    print(f"[-] Ошибка импорта: {e}. Проверь, нет ли в firmware_handler.py лишних импортов.")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

async def run_test():
    print("=== ТЕСТ РЕГУЛЯТОРА: ВЫПУСК СЕРТИФИКАТА ===\n")

    # Создаем заглушки для зависимостей
    cert_manager = CertificateManager(
        storage_path="certificates.json", 
        private_key_path="keys/regulator_private.pem"
    )
    
    test_runner = MagicMock()
    test_runner.run_tests = AsyncMock(return_value={"passed": True})
    
    coverage_controller = MagicMock()
    broker = MagicMock()
    broker.publish = AsyncMock()

    # Инициализируем обработчик
    handler = FirmwareHandler(cert_manager, test_runner, coverage_controller, broker)

    # Тестовые данные запроса
    test_payload = {
        "request_id": "REQ-AGRO-2026",
        "hack": True,
        "timestamp": "2026-03-26T15:50:00", # Время
        "developer_id": "AgroTech_Global",   # Разработчик
        "drone_type": "T40-Sprayer",         # Тип дрона
        "firmware": {
            "commit_hash": "abc12345",
            "repository_url": "http://github.com"
        }
    }


    print(f"[*] Отправка запроса: {test_payload['request_id']}")
    
    await handler.handle(test_payload)
    
    print("\n[OK] Если выше в логах есть 'certified', значит тест пройден!")

if __name__ == "__main__":
    asyncio.run(run_test())
