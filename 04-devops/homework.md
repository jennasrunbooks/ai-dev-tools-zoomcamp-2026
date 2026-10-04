## Question 1: Run the app

Start Order Tracker with `docker compose up --build -d --wait`, then check `curl http://localhost:8000/healthz`.

What does the health check return?

> 💡 **Answer:** `{"status":"ok"}`

## Question 2: Instrument one endpoint

Ask your agent to add OpenTelemetry metrics, logs, and traces for order lookups, including route and HTTP status code on the request metric, exported to the console for now.

Rebuild, then look up order `standard-1001` (`curl -i http://localhost:8000/api/orders/standard-1001`) and find the request metric in `docker compose logs app`.

Which HTTP status code does the metric record for this lookup?

> 💡 **Answer:** `200`

## Question 3: Build the telemetry pipeline

Ask your agent to add an OpenTelemetry Collector, Prometheus, Loki, Tempo, and Grafana to Docker Compose, routing the app's metrics/logs/traces through the Collector, plus a Grafana dashboard for request counts and errors. Save the config in the repo.

Rebuild, look up order `standard-1002`, and find its request metric (and matching log/trace) in Grafana.

Which HTTP status code does the metric show?

> 💡 **Answer:** `404`

## Question 4: Configure the alert

Ask your agent to add a Grafana alert on the `5xx` metric, including the endpoint, time window, and dashboard link, and handling no-data periods. Re-run the Question 3 lookup and wait for the alert to evaluate.

What state does Grafana show?

> 💡 **Answer:** `Normal`

## Question 5: Build the automatic responder

Ask your agent to build a service in `incident-response/` that receives Grafana alerts at `POST /alerts` on port `8001`, saves evidence (affected endpoint, logs, traces), and starts the coding assistant automatically in headless mode.

Start the responder and send it a test alert:

```bash
curl -X POST http://localhost:8001/alerts \
  -H 'Content-Type: application/json' \
  -d '{"alerts":[{"status":"firing","labels":{"alertname":"ResponderTest","test":"true"},"annotations":{"summary":"Test notification; no incident to fix"}}]}'
```

What did the agent respond? Include the last line from its answer.

> 💡 **Answer:** `Test alert — no incident, no root cause, no code changes made.`

## Question 6: Watch the agent fix the incident

Connect the Grafana alert to the responder via webhook, then trigger the bug with `curl -i http://localhost:8000/api/orders/express-1002` (repeat if it doesn't fire immediately). Watch the webhook reach `/alerts` and the responder start automatically.

Wait for the agent to fix the problem, restart the app, and confirm the same request no longer fails.

What was the problem?

> 💡 **Answer:** `ValueError: day is out of range for month`

**Incident evidence** — `docker compose logs incident-response` output from the run that fixed it:

```
incident-response-1  | INFO:incident_response:starting headless agent for alert=Order Tracker 5xx errors
incident-response-1  | INFO:incident_response:agent response for alert=Order Tracker 5xx errors: Confirmed. The old code raised `ValueError` for the `express-1002` seed order (placed Sept 30 → `day=32`), producing the 500s; the fix correctly computes Oct 2.
incident-response-1  |
incident-response-1  | **Root cause:** `order_detail()` computed express orders' estimated delivery with `placed_at.replace(day=placed_at.day + 2)`, which raises `ValueError: day is out of range for month` when the order date is within 2 days of month-end. The seeded `express-1002` order is dated the last day of the previous month, so every lookup of it returned HTTP 500 — matching the alert (route `/api/orders/{order_id}`, ~0.048 5xx rate) and the logs showing successful "order lookup hit" on `express-1002` immediately before the error.
incident-response-1  |
incident-response-1  | **Fix:** Replaced the unsafe `.replace(day=...)` with `placed_at + timedelta(days=2)`, which correctly rolls over month and year boundaries.
incident-response-1  |
incident-response-1  | Fixed a real bug: express-order estimated-delivery calculation in `app/main.py` crashed with 500s at month boundaries; replaced `.replace(day=day+2)` with `timedelta(days=2)`.
incident-response-1  | INFO:     10.215.24.4:42620 - "POST /alerts HTTP/1.1" 200 OK
```

Verified: `curl -i http://localhost:8000/api/orders/express-1002` returned `200` after the fix, with no docker restart command run anywhere in the loop (the app auto-reloaded off the shared `app/` mount).
