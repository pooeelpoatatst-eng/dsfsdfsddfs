from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken


class SessionCrypto:
    def __init__(self, key: str) -> None:
        try:
            self._fernet = Fernet(key.encode())
        except (ValueError, TypeError) as exc:
            raise ValueError("SESSION_ENCRYPTION_KEY must be a valid Fernet key") from exc

    def encrypt(self, session: str) -> str:
        return self._fernet.encrypt(session.encode()).decode()

    def decrypt(self, encrypted: str) -> str:
        try:
            return self._fernet.decrypt(encrypted.encode()).decode()
        except InvalidToken as exc:
            raise ValueError("Stored session cannot be decrypted") from exc
