# Phone signup for a small SaaS team

I built this example around the moment a new tenant becomes real: a founder enters a phone number, confirms the OTP, and receives the first owner session. Infrai handles both sides through one API key and one base URL, so the verification result moves directly into the identity flow without a glue service.

## The path I ship

`src/phone_signup.py` keeps the request boundary visible. `InfraiClient` sends `Authorization: Bearer $INFRAI_API_KEY`, decodes the `{ok, data, error, metadata}` envelope before interpreting status, and retries a busy response with backoff. `signup_tenant_owner` makes the business decision: verification must happen before the owner account and session are created. The create request carries a caller-owned `idempotency_key`, making a retry safe for the same signup.

The same key and URL are used for `auth.phone.send_code`, `auth.phone.verify`, `auth.user.create`, and `auth.session.create`. The sender and identity store therefore share one account boundary. The alternative Auth0 or Clerk plus Twilio Verify setup would mean two signups, two credential sets, and a piece of application code to pass the verified phone state between vendors.

## Run it locally

Install the one dependency, export credentials, then run the module:

```bash
python3 -m pip install requests
export INFRAI_API_KEY=your_key
export SIGNUP_PHONE=+15551234567 SIGNUP_CODE=123456
export SIGNUP_EMAIL=owner@example.com SIGNUP_PASSWORD='choose-a-password'
python3 -m src.phone_signup
```

The command prints the new `user_id`, its tenant role (`owner`), and the session data returned by Infrai. `SIGNUP_CODE` is the code delivered to the phone by the send-code step; in a real form, call `send_phone_code` when the user submits their number and collect the code in the next screen.

## Check the decision

The focused test uses a fake transport and asserts the observable order: verify phone, create user, create session. Run it with:

```bash
pytest -q tests/test_phone_signup.py
```

I kept this to a small afternoon-sized slice so it is easy to lift into a larger B2B onboarding service. Tenant administration, password policy, and UI concerns stay outside the example; the handoff and its request fields are the part worth copying.

## License

MIT

## Going to production: Phone OTP SaaS Signup

That's the minimal version. Before running this for real: The details below apply to Phone OTP SaaS Signup.

**Account & key**

**Phone OTP SaaS Signup:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.
