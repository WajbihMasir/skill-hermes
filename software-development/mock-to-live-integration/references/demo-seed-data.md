# Demo Seed Data (making a live-mode UI look real)

The UI has been switched to real mode but the database is empty or flat: every
screen shows an empty state, and dashboards read 0% or 100%. This is the recipe
for populating a live database with demo data that exercises every screen the
demo touches.

## When to seed through the API vs. direct DB insert

| Data | How | Why |
|---|---|---|
| Anything a real user flow could create (create event, assign task, upload evidence) | POST through the live API | Proves the whole path; doubles as a smoke test |
| Backdated history (events last week, an audit trail that looks lived-in) | Direct insert | Endpoints stamp the current time |
| Terminal states behind multi-step flows (VERIFIED evidence, resolved+verified issue) | Direct insert | Reproducing the full review chain per row is slow and brittle |
| States no endpoint assigns (OVERDUE assignment, a PENDING_REVIEW row left for the self-review demo) | Direct insert | No code path sets them |
| Append-only rows (audit logs behind an immutability trigger) | Direct insert | INSERT is the only permitted verb anyway |
| Notifications with custom timestamps / read flags | Direct insert | Endpoint-generated ones all look identical and fresh |

Either way, **verify through the read APIs the UI uses** (public homepage,
per-role dashboards, list endpoints, notification counts, audit query) — not by
re-querying the DB. Serialization, joins, and computed metrics are exactly what
the demo exercises.

## Idempotency: tag and recreate

- Tag every row the script owns with a recognizable prefix in a text column
  (e.g. name `"[DEMO] Tech Talk"`).
- Re-run = delete the previous tagged roots, flush, recreate. `ON DELETE
  CASCADE` on the child FKs removes requirements/tasks/issues/assignments with
  them — check the FK clauses before relying on this.
- Only rows reachable by cascade from a tagged root are cleaned. Notifications
  and audit rows keyed to old resource IDs survive; either clean them
  explicitly where allowed, or accept accumulation — decide, don't assume the
  delete covered them.
- Never touch shared entities: users/roles/permissions come from a separate
  user-seed script. Resolve them by email and fail loudly (with the fix
  command) when missing — the demo seed depends on the user seed having run
  first.
- Append-only tables cannot be cleaned (the immutability trigger rejects
  DELETE). Old audit rows from previous seed runs accumulate by design; accept
  it rather than fighting the trigger.

## Scenario coverage — one row per state the demo shows

Enumerate the states each screen renders and seed at least one row for each:

- **Dashboard metrics**: mixed statuses so numbers land in a realistic middle
  (e.g. compliance 42.86%, not 0% or 100%); include at least one overdue item
  and one event needing attention, or the "needs attention" panel is empty.
- **Self-review (SoD) demo**: leave one evidence row owned by the reviewer
  account in PENDING_REVIEW, so the reviewer can attempt it and hit the 403.
- **Re-upload demo**: at least one REJECTED assignment (upload is only allowed
  for NOT_STARTED / REJECTED).
- **Notification badge**: some unread notifications for each demo account.
- **Public homepage**: an event that falls on "today" per the backend's
  boundary rule (see timezone trap below).
- **Task/issue lists**: one row per status in the state machine, so filters and
  status badges all render.

Print a summary table at the end of the script (counts per entity) so a re-run
is self-describing.

## The timezone trap for "today"

If the backend computes "today" in UTC but the demo audience is UTC+7, seeding
"today 09:00" as local wall-clock time puts the event on the wrong UTC day and
the homepage shows nothing. Write one helper that converts an intended local
wall-clock time to UTC (e.g. `wib(days, hour)`) and use it for every timestamp.
General rule: compute the instant the BACKEND will classify as today, in the
backend's own timezone, then convert.

## Verification checklist after seeding

- Public/homepage endpoints: non-empty, metrics varied (not all 0/100).
- Each demo account's dashboard: assigned items, pending reviews, unread counts.
- List endpoints per role: the role sees the rows the demo needs.
- Audit query: the seeded history is visible with actor/IP.
- Login still works for every demo account (the seed never touches them).
