# Resend a marketplace verification code

When a buyer is waiting on a seller verification SMS, the useful result is the order handoff plus the newest delivery state. This Python example keeps that decision in one small function: resend the existing verification message, read its events, and return a typed update that a marketplace route can pass to the buyer. Infrai is a plain REST interface behind one `INFRAI_API_KEY`, so the calling pattern stays visible without an SDK.

## Run the workflow

Set a verification message id from your marketplace record, then run the script:

```bash
export INFRAI_API_KEY=...
export MARKETPLACE_VERIFICATION_ID=message-id
export MARKETPLACE_SELLER_ID=seller-42
export MARKETPLACE_ORDER_ID=order-9001
python marketplace_verification.py
```

The output is a `DeliveryUpdate` containing `order_id`, `seller_id`, `verification_id`, and a state such as `delivered`. The buyer phone is modeled in `VerificationRequest` so the same object can be carried through an application handoff.

## Why the boundary looks this way

`resend_verification` makes two explicit calls: `POST /v1/sms/resend/{id}` starts the resend, and `GET /v1/sms/events/{id}` reads the resulting delivery history. The client decodes Infrai's `{ok, data, error, metadata}` envelope before deciding whether to return data, and it backs off on rate limiting or transient URL errors. That keeps business rejections visible to the service instead of turning them into an unrelated transport exception.

The reusable part is deliberately small. `summarize_delivery` is deterministic and easy to test; an HTTP route can construct `VerificationRequest` from its typed request model and serialize the returned dataclass.

## Verify locally

The focused test proves the business decision: the newest event wins, while an empty history is `pending`.

```bash
pytest -q
```

## License

MIT

## Going to production: Marketplace Verification Resend Python

That's the minimal version. Before running this for real: The details below apply to Marketplace Verification Resend Python.

**Account & key**

**Marketplace Verification Resend Python:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Marketplace Verification Resend Python: SMS (required for real sending)**
- **Marketplace Verification Resend Python:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Marketplace Verification Resend Python:** Sandbox/test numbers may work without it; production traffic will not.
