import asyncio
import logging
import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

# 1. Пытаемся импортировать твои модели и менеджер
try:
    from models import FirmwareRequest, FirmwareResult
    from certificate_manager import CertificateManager
    from config import Config
except ImportError:
    # Если импорты не найдутся, тест создаст заглушки сам
    print("[!] Предупреждение: Модели не найдены, использую заглушки.")
    class FirmwareRequest:
        def __init__(self, **kwargs):
            self.request_id = kwargs.get("request_id", "TEST-ID")
            self.firmware = kwargs.get("firmware", {})
    class FirmwareResult:
        def __init__(self, **kwargs): self.data = kwargs
        def dict(self): return self.data
    Config = type('Config', (), {'TOPIC_FIRMWARE_RESULT': 'test_topic'})

# 2. Твой КЛАСС (FirmwareHandler)
class FirmwareHandler:
    def __init__(self, cert_manager, test_runner, coverage_controller, broker):
        self.cert_manager = cert_manager
        self.test_runner = test_runner
        self.coverage_controller = coverage_controller
        self.broker = broker
    
    async def handle(self, message: dict):
        try:
            req = FirmwareRequest(**message)
            logging.info(f"Processing firmware request {req.request_id}")
            
            # Имитируем проверку безопасности
            test_result = await self.test_runner.run_tests(req.firmware)
            if not test_result.get("passed", True):
                logging.warning("Security tests failed")
                return

            # Создание сертификата
            cert = self.cert_manager.create_certificate(
                subject_type="firmware",
                subject_id=req.firmware.get("commit_hash", "default_hash"),
                security_goals=["FW-SEC-01"]
            )
            
            logging.info(f"SUCCESS: Firmware {req.request_id} certified as {cert.certificate_id}")
            return cert
        except Exception as e:
            logging.error(f"Error: {e}")

# 3. ФУНКЦИЯ ТЕСТА (теперь с правильными отступами!)
# async def run_test():
#     print("\n=== ЗАПУСК ТЕСТА РЕГУЛЯТОРА (ФИНАЛ) ===")
#     logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

#         # 1. Сначала читаем сам ключ из файла
#     try:
#         with open("keys/regulator_private.pem", "r") as f:
#             secret_key_content = f.read().strip()
#         print("[+] Файл ключа успешно прочитан")
#     except FileNotFoundError:
#         print("[-] ОШИБКА: Файл keys/regulator_private.pem не найден!")
#         return

#     # 2. Теперь создаем менеджер, передавая строку ключа третьим аргументом
#     try:
#         cert_manager = CertificateManager(
#             "certificates.json",      # путь к базе сертификатов
#             "crl.json",               # путь к списку отозванных
#             secret_key_content        # САМ ТЕКСТ КЛЮЧА (а не путь!)
#         )
#         print("[+] CertificateManager готов к работе")
#     except Exception as e:
#         print(f"[-] ОШИБКА ИНИЦИАЛИЗАЦИИ: {e}")
#         return


#     # Заглушки
#     test_runner = MagicMock()
#     test_runner.run_tests = AsyncMock(return_value={"passed": True})
#     broker = MagicMock()
#     broker.publish = AsyncMock()

#     # Запуск
#     handler = FirmwareHandler(cert_manager, test_runner, MagicMock(), broker)
#     test_payload = {
#         "request_id": "REQ-AGRO-2026",
#         "hack": True,
#         "timestamp": "2026-03-26T15:50:00", # Время
#         "developer_id": "AgroTech_Global",   # Разработчик
#         "drone_type": "T40-Sprayer",         # Тип дрона
#         "firmware": {
#             "commit_hash": "abc12345",
#             "repository_url": "http://github.com"
#         }
#     }

#     await handler.handle(test_payload)
#     print("=== ТЕСТ ЗАВЕРШЕН ===\n")

async def run_test():
    print("\n=== ЗАПУСК ТЕСТА РЕГУЛЯТОРА (ФИНАЛ + REVOKE) ===")
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    # 1. Читаем ключ
    try:
        with open("keys/regulator_private.pem", "r") as f:
            secret_key_content = f.read().strip()
    except FileNotFoundError:
        print("[-] ОШИБКА: Файл ключа не найден!")
        return

    # 2. Создаем менеджер
    cert_manager = CertificateManager("certificates.json", "crl.json", secret_key_content)
    
    # 3. Заглушки
    test_runner = MagicMock()
    test_runner.run_tests = AsyncMock(return_value={"passed": True})
    broker = MagicMock()
    broker.publish = AsyncMock()

    # 4. Инициализация и СОЗДАНИЕ сертификата
    handler = FirmwareHandler(cert_manager, test_runner, MagicMock(), broker)
    test_payload = {
        "request_id": "REQ-AGRO-2026",
        "timestamp": "2026-03-26T15:50:00",
        "developer_id": "AgroTech_Global",
        "drone_type": "T40-Sprayer",
        "firmware": {"commit_hash": "abc12345"}
    }

    # ВАЖНО: сохраняем результат в переменную cert
    cert = await handler.handle(test_payload)

    if cert:
        print(f"\n[*] Сертификат создан: {cert.certificate_id}")
        
        # 5. ТЕСТ ОТЗЫВА (REVOKE)
        print(f"[*] Отзываем сертификат...")
        cert_manager.revoke_certificate(cert.certificate_id)

        # 6. ПРОВЕРКА
        if cert.certificate_id in cert_manager.crl:
            print("[OK] Сертификат успешно добавлен в CRL (черный список)!")
        
        is_valid = cert_manager.verify_certificate(cert)
        print(f"[*] Результат проверки после отзыва: {'Валиден' if is_valid else 'ЗАБЛОКИРОВАН'}")
    
    print("\n=== ТЕСТ ЗАВЕРШЕН ===")


# 4. ТОЧКА ВХОДА (на самом краю, без отступов!)
if __name__ == "__main__":
    asyncio.run(run_test())
