import logging
import sys
import requests
from pythonjsonlogger import jsonlogger

# Данные для интеграции (Задача 2)
API_URL = "https://droneanalytics.ourpaint.ru/api/log/event"
API_KEY = "KBlD33rKRCGJw1hcTJ4Msy504gappn5vx58SGzUxr5bEgTzNCpOR2XfnpyzKec3nibpeuc7J6sf0KiyKgu8QQ60LZprr9a90Xvf8O6ECZKlgO8E5DsD3t5YHgEqf3IE9"
class RemoteHTTPHandler(logging.Handler):
    def emit(self, record):
        import datetime
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # СТРОГО СПИСОК [ { ... } ]
        payload = [{
            "timestamp": timestamp,
            "event": str(record.msg),
            "severity": record.levelname,
            "component": "regulator",
            "details": self.format(record)
        }]
        
        token = "KBlD33rKRCGJw1hcTJ4Msy504gappn5vx58SGzUxr5bEgTzNCpOR2XfnpyzKec3nibpeuc7J6sf0KiyKgu8QQ60LZprr9a90Xvf8O6ECZKlgO8E5DsD3t5YHgEqf3IE9"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            res = requests.post(API_URL, json=payload, headers=headers, timeout=5)
            print(f">>> Log Status: {res.status_code} ({res.reason})")
            if res.status_code in [200, 201]:
                print("✅ ВСЁ! Задача 2 выполнена, логи на сервере.")
            else:
                print(f">>> Server Response: {res.text}")
        except Exception as e:
            print(f">>> Log Send Error: {e}")

def setup_logging():
    logger = logging.getLogger()
    
    # 1. Оставляем твой вывод в консоль
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # 2. Добавляем интеграцию с сервером (Задача 2)
    remote_handler = RemoteHTTPHandler()
    remote_handler.setFormatter(formatter)
    logger.addHandler(remote_handler)

    logger.setLevel(logging.INFO)
    return logger

if __name__ == "__main__":
    # Тест интеграции
    log = setup_logging()
    log.info("INTEGRATION_TEST", extra={"status": "checking_task_2"})
    print("Проверь статус отправки в консоли выше (если добавишь print в emit)")