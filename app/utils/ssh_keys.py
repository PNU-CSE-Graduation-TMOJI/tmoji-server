# utils/ssh_keys.py
import os, stat
from typing import Tuple, Optional
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

def ensure_ed25519_key(path: str, passphrase: Optional[str] = None) -> Tuple[str, str]:
    """
    path: 개인키 저장 경로(예: /run/secrets/gpu_id_ed25519) - 확장자는 상관없음
    passphrase: 개인키 암호화(옵션). None이면 암호없이 저장.
    반환: (private_path, public_path)
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pub = path + ".pub"

    if not os.path.exists(path):
        key = Ed25519PrivateKey.generate()

        # 개인키를 OpenSSH 포맷으로 저장 ("-----BEGIN OPENSSH PRIVATE KEY-----")
        enc = (serialization.BestAvailableEncryption(passphrase.encode())
               if passphrase else serialization.NoEncryption())

        with open(path, "wb") as f:
            f.write(
                key.private_bytes(
                    encoding=serialization.Encoding.PEM,          # 아스키 아머
                    format=serialization.PrivateFormat.OpenSSH,   # OpenSSH 개인키 포맷
                    encryption_algorithm=enc
                )
            )
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)  # 600

        # 공개키를 OpenSSH 포맷으로 저장 ("ssh-ed25519 AAAA... comment")
        with open(pub, "wb") as f:
            f.write(
                key.public_key().public_bytes(
                    encoding=serialization.Encoding.OpenSSH,
                    format=serialization.PublicFormat.OpenSSH,
                )
            )
            f.write(b" worker@container\n")  # 코멘트

    return path, pub
