import pytest

from app.modules.webshot import public_url


def test_webshot_accepts_public_url() -> None:
    assert public_url("https://example.com/page").startswith("https://example.com")


def test_webshot_rejects_local_url() -> None:
    with pytest.raises(ValueError):
        public_url("http://127.0.0.1/admin")
