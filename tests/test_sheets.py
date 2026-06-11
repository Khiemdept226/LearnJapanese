import json

import sheets


def test_get_client_uses_service_account_json_env(monkeypatch):
    service_account = {
        "type": "service_account",
        "project_id": "learnjp",
        "private_key_id": "key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----\n",
        "client_email": "bot@example.iam.gserviceaccount.com",
        "client_id": "123",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/bot",
    }
    calls = {}

    class FakeCredentials:
        @classmethod
        def from_service_account_info(cls, info, scopes):
            calls["info"] = info
            calls["scopes"] = scopes
            return "credentials"

    monkeypatch.setattr(sheets, "GOOGLE_SERVICE_ACCOUNT_JSON", json.dumps(service_account))
    monkeypatch.setattr(sheets, "Credentials", FakeCredentials)
    monkeypatch.setattr(sheets.gspread, "authorize", lambda credentials: {"authorized_with": credentials})

    client = sheets.get_client()

    assert client == {"authorized_with": "credentials"}
    assert calls["info"] == service_account
    assert calls["scopes"] == sheets.SCOPES
