import ssl
import os

def check_certs():
    cert_file = "server.crt"
    key_file = "server.key"
    
    if not os.path.exists(cert_file) or not os.path.exists(key_file):
        print("❌ Файлы сертификатов не найдены!")
        return False
    
    try:
        # Пытаемся загрузить их в SSL-контекст. 
        # Если ключ не подходит к сертификату, Python выдаст ошибку.
        context = ssl.create_default_context()
        context.load_cert_chain(certfile=cert_file, keyfile=key_file)
        print("✅ Валидация TLS: Ключ и сертификат соответствуют друг другу.")
        return True
    except ssl.SSLError as e:
        print(f"❌ Ошибка валидации: {e}")
        return False

if __name__ == "__main__":
    check_certs()