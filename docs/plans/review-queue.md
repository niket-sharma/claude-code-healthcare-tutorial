# Plan: Clinician Review Queue

Source spec: `/home/niket/ai/claude-code-healthcare-tutorial/docs/specs/review-queue.md`

## Context (observed in codebase)

- ORM uses **SQLModel** (`sqlmodel`), not raw async SQLAlchemy. The encounter
  model lives at `/home/niket/ai/claude-code-healthcare-tutorial/app/models/encounter.py`
  and uses `SQLModel, table=True`.
- DB access is **synchronous** via `Session` from
  `/home/niket/ai/claude-code-healthcare-tutorial/app/core/db.py`
  (`engine`, `get_session()`, `create_db_and_tables()`). There is no async
  session in this repo despite the CLAUDE.md description; follow the **actual**
  pattern in `db.py` (sync `Session`) so the queue insert and triage write can
  share one transaction. Do not introduce async SQLAlchemy here.
- Triage logic is in
  `/home/niket/ai/claude-code-healthcare-tutorial/app/services/triage.py`
  (`triage()` returns a `TriageResult` with `triage_level`, `rationale`,
  `disclaimer`). Red-flag escalations produce `triage_level == "seek_immediate_care"`.
- The deterministic red-flag gate is
  `/home/niket/ai/claude-code-healthcare-tutorial/app/core/red_flags.py`. This
  plan must NOT modify it (out of scope per spec).
- The shared disclaimer string is defined in `triage.py` and `red_flags.py` and
  on the `Encounter` model default.
- Convention: one router per resource in `app/api/`, Pydantic v2 schemas
  alongside the route, `201` for creates, disclaimer on every response.

> NOTE FOR IMPLEMENTER: confirm the exact filename of the FastAPI app entry
> point and the existing POST-encounter / triage router before Task 7 and
> Task 8. Search for `FastAPI(` and `include_router(` to locate them. Tasks
> below reference the conventional paths (`app/main.py`, `app/api/encounters.py`);
> adjust to the real filenames if they differ. Do not change behavior of the
> existing encounter persistence beyond adding the enqueue step.

---

### Task 1 — Add the `review_queue` SQLModel model
**What:** Create a `ReviewQueue` SQLModel table model with the fields and
constraints from the spec.
**Files:** create `/home/niket/ai/claude-code-healthcare-tutorial/app/models/review_queue.py`
**Done when:** A `ReviewQueue(SQLModel, table=True)` class exists with:
`id` (int PK, optional/autoincrement), `encounter_id` (int, FK to `encounter.id`,
**unique**), `created_at` (datetime, default factory `datetime.utcnow`),
`review_status` (str, default `"pending"`), `reviewed_at` (Optional[datetime],
default None), `reviewed_by` (Optional[str], default None). The `encounter_id`
field is declared `unique=True` and as a foreign key to `encounter.id`. No logic,
no network, no PHI in defaults.

### Task 2 — Ensure the table is created at startup
**What:** Make sure `ReviewQueue` is imported before `create_db_and_tables()`
runs so SQLModel registers it in `SQLModel.metadata`.
**Files:** edit the module that calls `create_db_and_tables()` (the FastAPI app
entry point, conventionally `/home/niket/ai/claude-code-healthcare-tutorial/app/main.py`)
and/or `/home/niket/ai/claude-code-healthcare-tutorial/app/models/__init__.py`
**Done when:** Importing the app and calling `create_db_and_tables()` against a
fresh SQLite file produces a `review_queue` table (verifiable by inspecting
`SQLModel.metadata.tables` or the SQLite schema). No existing tables are dropped
or altered.

### Task 3 — Define a pure "should this be queued?" predicate
**What:** Add a small deterministic helper that returns True when a triage level
is queue-eligible (`"urgent"` or `"seek_immediate_care"`), else False.
**Files:** add to the enqueue service module created in Task 4 (e.g.
`/home/niket/ai/claude-code-healthcare-tutorial/app/services/review_queue.py`)
**Done when:** The helper returns True only for `"urgent"` and
`"seek_immediate_care"`, and False for `"self_care"` and `"see_clinician"`. It
is pure (no DB, no network, no logging) and unit-testable in isolation.

### Task 4 — Add the enqueue service function (same-transaction insert)
**What:** Add a service function that, given a `Session` and a persisted
encounter (with its `id` and `triage_level`), inserts a `ReviewQueue` row when
the predicate from Task 3 is True, using the **same** `Session`/transaction the
caller used to persist the encounter.
**Files:** create `/home/niket/ai/claude-code-healthcare-tutorial/app/services/review_queue.py`
**Done when:** The function (a) accepts the active `Session` rather than opening
its own, (b) adds a `ReviewQueue` row only for queue-eligible levels, (c) does
NOT call `session.commit()` itself (commit is owned by the caller so the queue
insert and encounter write commit or roll back together), and (d) emits no log
or print containing `symptoms_text`, `rationale`, or other encounter detail.
**SAFETY CHECK (atomicity):** The function must operate on the caller's
transaction so that if the queue insert fails, the encounter write rolls back
too. It must never start, commit, or close an independent session/transaction.

### Task 5 — Wire enqueue into the encounter-creation flow with rollback-to-503
**What:** In the existing POST endpoint that persists a triage encounter, after
adding the encounter to the session and obtaining its `id` (flush, not commit),
call the enqueue service within the **same** transaction, then commit once.
**Files:** edit the existing encounter/triage creation route (conventionally
`/home/niket/ai/claude-code-healthcare-tutorial/app/api/encounters.py`; confirm
real filename)
**Done when:** For a queue-eligible triage result, a single commit persists both
the encounter and its queue row. If the enqueue (or the combined commit) raises,
the handler rolls back the transaction (no orphan encounter) and returns HTTP
`503`. Non-eligible levels persist the encounter only, with no queue row, and
return the existing success status. The success response still includes the
`disclaimer` field.
**SAFETY CHECK (no lost urgent encounter):** Verify there is no code path where
an `urgent` / `seek_immediate_care` encounter commits without its queue row. The
encounter `id` must be obtained via flush before enqueue so the FK is valid, and
both writes must share one commit.

### Task 6 — Pydantic v2 schemas for the review-queue resource
**What:** Define request/response schemas: a list-item response (queue fields +
derived encounter fields + `disclaimer`), a list envelope (`items`, `total`),
and a PATCH request body (`reviewed_by: Optional[str]`).
**Files:** add schemas alongside the new router (e.g. inside
`/home/niket/ai/claude-code-healthcare-tutorial/app/api/review_queue.py` or a
`schemas.py` sibling), Pydantic v2 style
**Done when:** The item schema exposes exactly: `id`, `encounter_id`,
`created_at`, `review_status`, `reviewed_at`, `reviewed_by`,
`encounter_created_at`, `age`, `sex`, `symptoms_text`, `triage_level`,
`rationale`, `disclaimer`. The list response is `{ "items": [...], "total": int }`.
The PATCH body makes `reviewed_by` optional. Schemas validate under Pydantic v2.

### Task 7 — Implement `GET /review-queue` (list, filter, paginate, sort)
**What:** Add a router with `GET /review-queue` that joins `review_queue` to
`encounter`, filters by `status`, paginates, sorts newest-first by queue
`created_at`, and returns `items` + `total`.
**Files:** create `/home/niket/ai/claude-code-healthcare-tutorial/app/api/review_queue.py`
**Done when:** `status` defaults to `pending` and accepts `pending` | `reviewed`
| `all` (other values -> `422`); `limit` defaults to 20 with `1 <= limit <= 100`
(out of range -> `422`); `offset` defaults to 0 with `offset >= 0` (negative ->
`422`); results are ordered by queue `created_at` descending; `total` reflects
all rows matching the status filter **before** limit/offset; every item includes
`disclaimer`; encounter fields are read from the joined encounter (the encounter
remains source of truth). Returns `200`.

### Task 8 — Implement `PATCH /review-queue/{id}/reviewed` (idempotent, encounter-immutable)
**What:** Add `PATCH /review-queue/{queue_item_id}/reviewed` that sets
`review_status = "reviewed"`, sets `reviewed_at`, optionally records
`reviewed_by`, and returns the updated item in the same shape as the list item.
**Files:** edit `/home/niket/ai/claude-code-healthcare-tutorial/app/api/review_queue.py`
**Done when:** A pending item becomes `reviewed` with `reviewed_at` set; missing
`queue_item_id` returns `404`; invalid path/body returns `422`; calling on an
already-reviewed item is idempotent (stays `reviewed`, preserves original
`reviewed_at` unless explicitly documented otherwise); response includes the
joined encounter fields and `disclaimer`; returns `200`.
**SAFETY CHECK (encounter immutability):** The handler must update ONLY the
`review_queue` row. It must never `add`, `update`, or `delete` the `Encounter`
object, and must not change the encounter's `triage_level`, `rationale`,
`disclaimer`, `symptoms_text`, or `created_at`. Confirm no write to the
`encounter` table occurs in this code path.

### Task 9 — Register the review-queue router on the app
**What:** Include the new router in the FastAPI application.
**Files:** edit the FastAPI app entry point (conventionally
`/home/niket/ai/claude-code-healthcare-tutorial/app/main.py`; confirm real
filename)
**Done when:** `GET /review-queue` and `PATCH /review-queue/{id}/reviewed`
appear in the OpenAPI schema (`/openapi.json`) and are reachable; existing routes
are unchanged.

### Task 10 — Tests: enqueue trigger and atomicity
**What:** Add pytest tests covering queue creation rules and transactional
atomicity.
**Files:** create `/home/niket/ai/claude-code-healthcare-tutorial/tests/test_review_queue_enqueue.py`
**Done when:** Tests assert: (a) `urgent` encounter creates exactly one queue
row linked by `encounter_id`; (b) `seek_immediate_care` (red-flag) creates
exactly one queue row; (c) `self_care` and `see_clinician` create zero queue
rows; (d) duplicate enqueue for the same `encounter_id` is rejected by the unique
constraint; (e) when enqueue fails, no encounter row remains and the API returns
`503`. All fixtures use synthetic data only.
**SAFETY CHECK (logging):** Include an assertion or review note that the enqueue
path emits no log/print containing `symptoms_text` or `rationale`.

### Task 11 — Tests: `GET /review-queue` listing, filtering, pagination
**What:** Add pytest tests for list behavior.
**Files:** create `/home/niket/ai/claude-code-healthcare-tutorial/tests/test_review_queue_list.py`
**Done when:** Tests assert: default returns only `pending`, newest-first;
`status=reviewed` returns only reviewed; `status=all` returns both; `limit`/
`offset` validation returns `422` for out-of-range values; `total` reflects all
matching rows before pagination; every item contains `disclaimer`. Synthetic
data only.

### Task 12 — Tests: PATCH reviewed, 404, idempotency, encounter immutability
**What:** Add pytest tests for the PATCH endpoint.
**Files:** create `/home/niket/ai/claude-code-healthcare-tutorial/tests/test_review_queue_patch.py`
**Done when:** Tests assert: marking a pending item sets `review_status ==
"reviewed"` and `reviewed_at`; PATCH on missing id returns `404`; invalid body
returns `422`; a second PATCH is idempotent; and — the load-bearing safety
assertion — the linked encounter's `triage_level`, `rationale`, `disclaimer`,
`symptoms_text`, and `created_at` are byte-for-byte unchanged before vs. after
the PATCH. Synthetic data only.

---

## Safety summary (consolidated)

1. **Atomicity (Task 4, Task 5, Task 10):** the queue insert shares the
   encounter write's transaction; if it fails, both roll back and the caller
   gets `503`. No urgent encounter is ever persisted without its queue row.
2. **Encounter immutability on review (Task 8, Task 12):** PATCH
   `/review-queue/{id}/reviewed` must never write to the `encounter` table.
3. **No PHI in logs (Task 4, Task 10):** no new log/print may emit
   `symptoms_text`, `rationale`, or other encounter detail.
4. **Disclaimer preserved (Task 6, Task 7, Task 8, Task 11):** every surfaced
   item carries the disclaimer.
5. **Red-flag module untouched:** `app/core/red_flags.py` is out of scope and
   must not be modified.
6. **Synthetic data only** in all tests and examples.
