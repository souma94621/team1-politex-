from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import os

BASE_DIR = os.path.dirname(__file__)
KEY_DIR = os.path.join(BASE_DIR, "keys")

os.makedirs(KEY_DIR, exist_ok=True)

private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)

with open(os.path.join(KEY_DIR, "regulator_private.pem"), "wb") as f:
    f.write(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
    )

public_key = private_key.public_key()

with open(os.path.join(KEY_DIR, "regulator_public.pem"), "wb") as f:
    f.write(
        public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    )
