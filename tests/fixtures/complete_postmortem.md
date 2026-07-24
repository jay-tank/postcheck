# Incident: Checkout API outage

## Summary
On 2026-07-20, the checkout API returned 500 errors for 40 minutes, blocking all purchases.

## Timeline
- 14:02 UTC: Error rate spikes to 80%
- 14:05 UTC: Page fires, on-call engages
- 14:38 UTC: Root cause identified, rollback initiated
- 14:42 UTC: Error rate returns to baseline

## Root Cause
A database migration deployed at 14:00 UTC dropped an index that the checkout query
relied on, causing full table scans and connection pool exhaustion under load.

## Impact
~40 minutes of checkout downtime, an estimated 1,200 failed purchase attempts.

## Action Items
- Add a migration safety check for index drops on hot-path tables (@alice, due 2026-08-01)
- Add an alert on connection pool saturation (@bob, due 2026-07-30)

## What Went Well
On-call responded within 3 minutes of the page firing, and the rollback was clean.
