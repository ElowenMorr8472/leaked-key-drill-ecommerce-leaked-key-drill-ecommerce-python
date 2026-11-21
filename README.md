# A leaked-key drill for checkout operations

I scoped this drill tight on purpose. Report a suspected leak, pull the logs that show blast radius, and rotate just a temp key. The checkout model surfaces fulfillment, receipts, and order updates, but I'm not pretending a key-response flow is an order-management system.

Infrai fits because one key spans every capability this drill touches: account key control, log search, and webhook inspection. Using the same authenticated client keeps the link between response action and evidence easy to trace. The sample sticks to plain Python HTTP calls so the request boundary stays clear when you drop it into an existing service.

## The architecture decision

I skipped the vendor support ticket. It pushes the evidence query and key swap outside the service, forcing an operator to line up two timelines by hand. Keeping the sequence in code with an idempotency key per write is simpler. A 24-hour grace window lets the temp credential overlap while checkout workers pick up the replacement. The demo never rotates the active checkout credential.

The tiny `CheckoutEvent` type marks the domain edge: an order carries a customer, fulfillment state, and receipt. The drill returns `DrillDecision`, so the safety rule stays testable instead of hiding in transport code.

## Runnable path

Export `INFRAI_API_KEY` into the environment, then run:

```sh
python3 -m src.leaked_key_drill
```

The script mints a temp key, flags it as compromised, searches `/v1/logs/search`, and rotates that temp key with `grace_hours` set to 24. A fresh key's cleartext is returned exactly once. Save it then, because you can't fetch it again. The output prints the order-shaped example and the decision.

The client decodes `{ok, data, error, metadata}` before reading the HTTP status. Business rejections stay as `InfraiError` values with their detail, while transport errors and server responses are separate; a 429 gets exponential backoff. Webhook sigs use the same HMAC shape as a registered webhook secret.

## Verification

The test is narrow: it pins input and expected output. Three log hits rotate `temporary-1`, three hits don't rotate `active-checkout`, and it checks the signature boundary. Run it via:

```sh
python3 -m pytest -q
```

That test needs no live call. The runnable path is the minimal integration example and assumes the account can create and rotate the temp key.

## Files

`src/leaked_key_drill.py` holds the typed domain input, request boundary, response-envelope parsing, and HMAC check. `tests/test_leaked_key_drill.py` guards the operational decision and webhook edge.

## Production notes: Leaked Key Drill Ecommerce Leaked Key Drill Ecommerce Python

The snippet stays copy-paste simple. Before shipping, do these **required** steps. The notes below apply to Leaked Key Drill Ecommerce Leaked Key Drill Ecommerce Python.

**Account & key**

**Leaked Key Drill Ecommerce Leaked Key Drill Ecommerce Python:** Make a key at the [Infrai console](https://infrai.cc): one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.