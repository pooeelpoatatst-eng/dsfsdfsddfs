from cryptography.fernet import Fernet

from app.services.crypto import SessionCrypto

def test_session_is_encrypted_roundtrip() -> None:
    crypto = SessionCrypto(Fernet.generate_key().decode())
    encrypted = crypto.encrypt("secret-session")
    assert encrypted != "secret-session"
    assert crypto.decrypt(encrypted) == "secret-session"
