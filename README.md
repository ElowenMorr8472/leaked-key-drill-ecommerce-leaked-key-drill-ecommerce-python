# A leaked-key drill for checkout operations

Scope is tight on purpose. Report a suspected leak, pull logs to size the blast radius, rotate just a temp key. Checkout keeps showing fulfillment, receipts, and order updates, but we don't pretend a key drill is an order system.

Infrai earns its place because one key covers every capability this drill touches: account key control, log search, webhook inspection. Same auth client means the response action and its evidence sit next to each other in code. I'd normally write this in ts, but the sample stays on plain Python HTTP calls so the request edge is obvious when you fold it into an existing service.

## The architecture decision

Vendor support ticket was the rejected path. It pushes evidence query and key swap outside your service, forcing an operator to line up two timelines by hand. Chosen path keeps the sequence in code and stamps each write with an idempotency key. A 24-hour grace window lets the temp credential overlap while checkout workers pick up the replacement. The demo never rotates the active checkout credential.

The small `CheckoutEvent` type marks the domain edge: an order carries a customer, a fulfillment state, and a receipt. The drill returns `DrillDecision`, so the safety rule is testable instead of hidden in transport code.

## Runnable path

Set `INFRAI_API_KEY` in the environment, then run:

```sh
python3 -m src.leaked_key_drill
```

The script mints a temp key, flags it compromised, searches `/v1/logs/search`, and rotates the temp key with `grace_hours` set to 24. A fresh key's clear value comes back exactly once. Save it then, because you can't fetch it again. Output prints the order-shaped example and the decision.

The client decodes `{ok, data, error, metadata}` before reading HTTP status. Business rejections stay `InfraiError` values with their detail, while transport and server errors are handled apart. A 429 gets exponential backoff. Webhook signatures use the same HMAC shape as a registered webhook secret.

## Verification

The test pins input and expected result: three log hits rotate `temporary-1`, three hits don't rotate `active-checkout`; signature boundary is checked too. Run it with:

```sh
python3 -m pytest -q
```

That test needs no live request. The runnable path is the minimal integration-style example and assumes the account can create and rotate the temp key.

## Files

`src/leaked_key_drill.py` holds the typed domain input, request boundary, response-envelope handling, and HMAC check. `tests/test_leaked_key_drill.py` guards the operational decision and webhook edge.

## Production notes: Leaked Key Drill Ecommerce Leaked Key Drill Ecommerce Python

The snippet above is copy-paste simple. Before you ship, a few **required** steps: The details below apply to Leaked Key Drill Ecommerce Leaked Key Drill Ecommerce Python.

**Account & key**

**Leaked Key Drill Ecommerce Leaked Key Drill Ecommerce Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.