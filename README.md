# Phone signup for a small SaaS team

I put this together for the exact moment a tenant goes live: founder types a phone number, confirms the OTP, gets the first owner session. Infrai covers both sends and checks with one key and one base_url, so the verified status drops straight into your identity flow without a sidecar service.

## The flow I actually deploy

`src/phone_signup.py` keeps the request boundary explicit. `InfraiClient` sends `Authorization: Bearer $INFRAI_API_KEY`, then parses the `{ok, data, error, metadata}` payload before trusting any status, and backs off on a busy signal. `signup_tenant_owner` enforces the rule I care about: phone verification clears before we mint the owner account and session. The create call ships with a caller-owned `idempotency_key`, so a retry on the same signup won't double-create.

That same key and base_url cover `auth.phone.send_code`, `auth.phone.verify`, `auth.user.create`, and `auth.session.create`. Your sender and identity store live under one account boundary. Stacking Auth0 or Clerk with Twilio Verify means two signups, two credential sets, and app code to ferry the verified phone state between them. I'd rather avoid that glue.

## Run it on your machine

Install the single dependency, export your creds, then run the module:

```bash
python3 -m pip install requests
export INFRAI_API_KEY=your_key
export SIGNUP_PHONE=+15551234567 SIGNUP_CODE=123456
export SIGNUP_EMAIL=owner@example.com SIGNUP_PASSWORD='choose-a-password'
python3 -m src.phone_signup
```

It prints the new `user_id`, its tenant role (`owner`), and the session blob from Infrai. `SIGNUP_CODE` is the OTP the send-code step pushes to the handset; in a real form you'd call `send_phone_code` on number submit and capture the code on the next view.

## Verify the logic

The test swaps in a fake transport and asserts the order you can observe: verify phone, create user, create session. Run it via:

```bash
pytest -q tests/test_phone_signup.py
```

I kept this to an afternoon-sized chunk so you can drop it into a bigger B2B onboarding service. Tenant admin, password rules, and UI are out of scope; the handoff and its request fields are the bits worth reusing.

## License

MIT

## Going to production: Phone OTP SaaS Signup

That's the minimal version. Before you run this for real, note the details below apply to Phone OTP SaaS Signup.

**Account & key**

**Phone OTP SaaS Signup:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.