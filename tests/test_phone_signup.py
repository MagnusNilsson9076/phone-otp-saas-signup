from src.phone_signup import SignupResult, signup_tenant_owner


class FakeClient:
    def __init__(self):
        self.calls = []

    def verify_phone(self, phone, code, login=False):
        self.calls.append(("verify", phone, code, login))
        return {"verified": True}

    def create_user(self, email, password, name, idempotency_key):
        self.calls.append(("user", email, idempotency_key))
        return {"user_id": "usr_demo"}

    def create_session(self, user_id):
        self.calls.append(("session", user_id))
        return {"session_id": "sess_demo"}


def test_signup_verifies_phone_before_creating_owner_session():
    client = FakeClient()
    result = signup_tenant_owner(client, "+15551234567", "123456", "owner@example.com", "secret", "Owner", "signup-1")
    assert isinstance(result, SignupResult)
    assert result.user_id == "usr_demo"
    assert [call[0] for call in client.calls] == ["verify", "user", "session"]
    assert client.calls[0][3] is False
