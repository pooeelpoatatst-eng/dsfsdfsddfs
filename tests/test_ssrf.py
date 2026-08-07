import pytest

from app.services.downloader import UnsafeURLError, validate_public_url

def test_rejects_non_http_scheme() -> None:
    with pytest.raises(UnsafeURLError): validate_public_url("file:///etc/passwd")

def test_rejects_loopback_without_dns() -> None:
    with pytest.raises(UnsafeURLError): validate_public_url("http://127.0.0.1/private")
