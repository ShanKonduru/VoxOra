from __future__ import annotations

from types import SimpleNamespace

from app.services.storage_service import StorageService


class _FakeS3Client:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def put_object(self, **kwargs) -> None:
        self.calls.append(kwargs)


class _FakeClientContext:
    def __init__(self, client: _FakeS3Client) -> None:
        self._client = client

    async def __aenter__(self) -> _FakeS3Client:
        return self._client

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001, ANN201
        return None


class _FakeSession:
    def __init__(self, client: _FakeS3Client) -> None:
        self.client_instance = client

    def client(self, service_name: str, **kwargs):
        assert service_name == "s3"
        return _FakeClientContext(self.client_instance)


async def test_upload_audio_uses_expected_key_and_body(monkeypatch) -> None:
    fake_client = _FakeS3Client()
    service = StorageService()
    service._session = _FakeSession(fake_client)

    monkeypatch.setattr(
        "app.services.storage_service.settings",
        SimpleNamespace(
            s3_bucket="voxora-audio",
            s3_region="us-east-1",
            aws_access_key_id="minio-user",
            aws_secret_access_key="minio-pass",
            s3_endpoint_url="http://minio:9000",
        ),
    )

    url = await service.upload_audio("session-123", 2, b"webm-bytes")

    assert url == "http://minio:9000/voxora-audio/audio/session-123/q2.webm"
    assert fake_client.calls == [
        {
            "Bucket": "voxora-audio",
            "Key": "audio/session-123/q2.webm",
            "Body": b"webm-bytes",
            "ContentType": "audio/webm",
        }
    ]


async def test_upload_audio_returns_none_when_aioboto3_is_unavailable(monkeypatch) -> None:
    service = StorageService()
    service._session = None

    monkeypatch.setattr(
        "app.services.storage_service.settings",
        SimpleNamespace(
            s3_bucket="voxora-audio",
            s3_region="us-east-1",
            aws_access_key_id="minio-user",
            aws_secret_access_key="minio-pass",
            s3_endpoint_url="http://minio:9000",
        ),
    )

    url = await service.upload_audio("session-123", 2, b"webm-bytes")

    assert url is None