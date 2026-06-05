# Plan: GET /encounters endpoint

Paginated, newest-first list of encounters for the clinician dashboard.

## Context

- Research findings were provided inline by the requester; no standalone
  `docs/research/get-encounters-endpoint.md` exists in the repo.
- Source confirmed by reading:
  - `app/models/encounter.py` — flat `Encounter` SQLModel table; sort column is
    `created_at` (DESC).
  - `app/core/db.py` — synchronous `get_session()` generator, inject via
    `Depends(get_session)`.
  - `app/api/main.py` — routes currently hang directly on `app`; no `APIRouter`
    yet. `/triage` route already imports `Encounter`, `get_session`, `Session`.
  - `tests/test_triage_endpoint.py` — in-memory SQLite (`StaticPool`),
    `dependency_overrides[get_session]`, synchronous `TestClient`, class-based
    tests. Pattern to mirror in the new test file.

## Decisions (locked)

1. New router file `app/api/encounters.py` with
   `APIRouter(prefix="/encounters", tags=["encounters"])`.
2. Pagination via query params: `limit: int = Query(20, ge=1, le=100)` and
   `offset: int = Query(0, ge=0)`.
3. Response envelope `EncounterListResponse(items: list[EncounterRead], total: int)`.
4. `EncounterRead` Pydantic model exposing all `Encounter` fields with
   `disclaimer` mandatory (CLAUDE.md safety rule 1).
5. Wire into `app/api/main.py` via `app.include_router(...)`.

---

## Tasks (atomic, independently verifiable)

### Task 1 — Define `EncounterRead` schema
- **File:** `app/api/encounters.py` (new)
- **Do:** Create a Pydantic model `EncounterRead` mirroring every `Encounter`
  field: `id: int`, `created_at: datetime`, `age: int`, `sex: str`,
  `symptoms_text: str`, `triage_level: Optional[str]`, `rationale: Optional[str]`,
  `disclaimer: str` (required, not Optional). Set
  `model_config = ConfigDict(from_attributes=True)` so ORM rows convert directly.
- **Acceptance:** `EncounterRead.model_validate(encounter_orm_obj)` succeeds and
  carries a non-empty `disclaimer`. `disclaimer` is a required str (mypy/ruff and
  a `model_fields["disclaimer"].is_required()` check both confirm).

### Task 2 — Define `EncounterListResponse` envelope
- **File:** `app/api/encounters.py`
- **Do:** `class EncounterListResponse(BaseModel): items: list[EncounterRead]; total: int`.
- **Acceptance:** Model imports without error; `total` is an `int`, `items` is a
  list of `EncounterRead`.

### Task 3 — Create the router object
- **File:** `app/api/encounters.py`
- **Do:** `router = APIRouter(prefix="/encounters", tags=["encounters"])`.
- **Acceptance:** `from app.api.encounters import router` imports cleanly.

### Task 4 — Implement the GET handler
- **File:** `app/api/encounters.py`
- **Do:** Add `@router.get("", response_model=EncounterListResponse)` with
  `async def list_encounters(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), session: Session = Depends(get_session))`.
  - Query items:
    `session.exec(select(Encounter).order_by(Encounter.created_at.desc()).offset(offset).limit(limit)).all()`
  - Query total: `session.exec(select(func.count()).select_from(Encounter)).one()`
    (count over the full table, independent of limit/offset).
  - Return `EncounterListResponse(items=rows, total=total)`.
- **Notes:** `func` from `sqlmodel` (or `sqlalchemy`). Handler is `async def` per
  convention even though the session is synchronous (matches `/triage`).
- **Acceptance:** Endpoint returns 200 with `{items: [...], total: N}`; items are
  ordered `created_at` DESC; `total` reflects the whole table, not the page size.

### Task 5 — Wire the router into the app
- **File:** `app/api/main.py`
- **Do:** `from app.api.encounters import router as encounters_router` and, after
  `app = FastAPI(...)`, call `app.include_router(encounters_router)`.
- **Acceptance:** `GET /encounters` appears in the OpenAPI schema; app boots with
  no import-cycle errors (`main.py` already imports `Encounter`/`get_session`, so
  no circular import is introduced).

### Task 6 — Create the test file with fixtures
- **File:** `tests/test_encounters_endpoint.py` (new)
- **Do:** Copy the `session` and `client` fixtures from
  `tests/test_triage_endpoint.py` (in-memory `sqlite://`, `StaticPool`,
  `SQLModel.metadata.create_all`, `dependency_overrides[get_session]`, synchronous
  `TestClient`). Add a small helper to insert N synthetic `Encounter` rows with
  controlled, increasing `created_at` values so ordering is deterministic.
- **Synthetic data only:** Use obviously fictional symptoms (e.g. "test symptom 1")
  and plain ints for age — no real PHI (CLAUDE.md safety rule 2).
- **Acceptance:** Fixtures import and the empty-DB test below runs.

### Task 7 — Test: empty state
- **File:** `tests/test_encounters_endpoint.py`
- **Do:** With no rows inserted, `GET /encounters` returns 200,
  `items == []`, `total == 0`.
- **Acceptance:** Test passes.

### Task 8 — Test: newest-first ordering
- **File:** `tests/test_encounters_endpoint.py`
- **Do:** Insert >=3 rows with strictly increasing `created_at`. Assert the
  response `items` are returned in descending `created_at` order (most recent id
  first).
- **Acceptance:** Test passes; asserts on the actual order, not just length.

### Task 9 — Test: pagination math (limit + offset)
- **File:** `tests/test_encounters_endpoint.py`
- **Do:** Insert e.g. 5 rows. Request `?limit=2&offset=0` -> first 2 newest;
  `?limit=2&offset=2` -> next 2; `?limit=2&offset=4` -> last 1. In every case
  `total == 5`. Also assert `limit` boundary validation: `?limit=0` and
  `?limit=101` return 422; `?offset=-1` returns 422.
- **Acceptance:** All pagination slices correct and `total` constant; out-of-range
  params yield 422.

### Task 10 — Test: field presence + disclaimer on every item (SAFETY CHECK)
- **File:** `tests/test_encounters_endpoint.py`
- **Do:** Insert several rows. For every item in the response assert all expected
  keys are present and, critically, that `disclaimer` is present and non-empty
  on **each** item. Include at least one row whose `triage_level`/`rationale` are
  null to confirm those serialize while `disclaimer` stays populated.
- **Why safety:** CLAUDE.md safety rule 1 — every triage result surfaced via the
  API must carry the disclaimer. This endpoint is a new surface that exposes
  triage results, so the disclaimer guarantee must be enforced by test.
- **Acceptance:** Test fails if any item is missing `disclaimer` or it is empty.

### Task 11 — Logging / PHI safety check (SAFETY CHECK)
- **Files:** `app/api/encounters.py` (review), `app/services/triage.py` (review only)
- **Do:** Verify the new endpoint does **not** add any `logger`/`print`/log
  statement that emits encounter fields (`symptoms_text`, `age`, `sex`,
  `rationale`) or the full request/response. The handler should log nothing about
  row contents.
- **Context to be aware of (do not change in this feature):**
  `app/services/triage.py:95` already logs raw model output
  (`logger.warning("Malformed JSON from OpenAI; raw=%r", raw)`). That is
  pre-existing and out of scope here; just do not replicate that pattern in the
  new list endpoint, which would otherwise dump every patient's symptom text into
  logs.
- **Acceptance:** No new log/print statements reference encounter content; grep of
  `app/api/encounters.py` for `log`/`print` is clean (or only logs non-PHI like a
  request count).

### Task 12 — Lint + format + full test run
- **Files:** all touched
- **Do:** Run from repo root:
  - `ruff check .`
  - `ruff format --check .`
  - `pytest tests/test_encounters_endpoint.py`
  - `pytest` (full suite — ensure `/triage` tests still green after `main.py` edit)
- **Lint notes:** keep imports sorted/grouped (ruff isort); use
  `from __future__ import annotations` only if matching neighboring style; no unused
  imports (e.g. drop `func` import if total is computed differently).
- **Acceptance:** Ruff clean, formatter clean, full suite passes.

---

## Files affected
- `app/api/encounters.py` — new (schemas + router + handler)
- `app/api/main.py` — add `include_router`
- `tests/test_encounters_endpoint.py` — new

## Out of scope
- Frontend: no UI yet; this response schema is the future frontend contract only.
- Any change to `app/core/red_flags.py`, the `/triage` route logic, or the
  `Encounter` model.
