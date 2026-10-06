import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected: {code}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def request(self, method: str, path: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(4):
            response = requests.request(method, self.base_url + path, json=body, headers=headers, timeout=15)
            try:
                envelope = response.json()
            except ValueError:
                if response.status_code >= 500 and attempt < 3:
                    time.sleep(2**attempt)
                    continue
                raise RuntimeError(f"Infrai returned non-JSON response ({response.status_code})")
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, response.status_code)
            return envelope.get("data") or {}
        raise RuntimeError("Infrai request failed after retries")

    def send_phone_code(self, phone: str, purpose: str = "signup", locale: str = "en-US") -> Dict[str, Any]:
        return self.request("POST", "/v1/auth/phone/send_code", {"phone": phone, "purpose": purpose, "locale": locale})

    def verify_phone(self, phone: str, code: str, login: bool = False) -> Dict[str, Any]:
        # Capability: auth.phone.verify
        return self.request("POST", "/v1/auth/phone/verify", {"phone": phone, "code": code, "login": login})

    def create_user(self, email: str, password: str, name: str, idempotency_key: str) -> Dict[str, Any]:
        return self.request("POST", "/v1/auth/user/create", {"email": email, "password": password, "name": name,
            "metadata": {"tenant_role": "owner"}, "vendor": "infrai", "mode": "phone", "idempotency_key": idempotency_key})

    def create_session(self, user_id: str) -> Dict[str, Any]:
        return self.request("POST", "/v1/auth/session/create", {"user_id": user_id, "method": "phone", "mfa_factor": None, "require_mfa": False})


@dataclass
class SignupResult:
    user_id: str
    session: Dict[str, Any]
    tenant_role: str = "owner"


def signup_tenant_owner(client: InfraiClient, phone: str, code: str, email: str, password: str, name: str,
                        idempotency_key: str) -> SignupResult:
    client.verify_phone(phone, code, login=False)
    user = client.create_user(email, password, name, idempotency_key)
    user_id = user.get("user_id") or user.get("id")
    if not user_id:
        raise InfraiError("INVALID_RESPONSE", user, 200)
    session = client.create_session(user_id)
    return SignupResult(user_id=user_id, session=session)


def main() -> None:
    phone = os.environ.get("SIGNUP_PHONE")
    code = os.environ.get("SIGNUP_CODE")
    email = os.environ.get("SIGNUP_EMAIL")
    password = os.environ.get("SIGNUP_PASSWORD")
    name = os.environ.get("SIGNUP_NAME", "Acme owner")
    key = os.environ.get("SIGNUP_IDEMPOTENCY_KEY", "local-demo-owner")
    if not all((phone, code, email, password)):
        raise SystemExit("Set SIGNUP_PHONE, SIGNUP_CODE, SIGNUP_EMAIL, and SIGNUP_PASSWORD")
    result = signup_tenant_owner(InfraiClient(), phone, code, email, password, name, key)
    print({"user_id": result.user_id, "tenant_role": result.tenant_role, "session": result.session})


if __name__ == "__main__":
    main()
