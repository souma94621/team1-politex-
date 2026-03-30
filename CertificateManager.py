# certificate_manager.py
import json
import hashlib
from datetime import datetime, timedelta

class CertificateManager:
    def __init__(self, storage_path, private_key_path):
        self.storage = storage_path  # просто файл или БД
        self.private_key = open(private_key_path).read()

    def create_certificate(self, subject_type, subject_id, security_goals, validity_days=365):
        cert_id = f"CERT-{subject_type.upper()}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{subject_id}"
        cert_data = {
            "certificate_id": cert_id,
            "issued_at": datetime.utcnow().isoformat(),
            "valid_until": (datetime.utcnow() + timedelta(days=validity_days)).isoformat(),
            "subject_type": subject_type,
            "subject_id": subject_id,
            "security_goals": security_goals,
        }
        # Подпись: хеш от JSON
        cert_str = json.dumps(cert_data, sort_keys=True)
        signature = hashlib.sha256((cert_str + self.private_key).encode()).hexdigest()
        cert_data["digital_signature"] = signature
        self._save(cert_data)
        return Certificate(**cert_data)

    def verify_certificate(self, certificate: Certificate) -> bool:
        # проверяем подпись и срок действия
        # ...
        pass

    def revoke_certificate(self, cert_id):
        # обновляем статус в хранилище
        pass