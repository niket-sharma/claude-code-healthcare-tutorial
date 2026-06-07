# Spec: Clinician Review Queue

## Summary

When a triage result requires urgent attention, the API must preserve the
original triage record and also create a clinician-facing review queue item.
Clinicians can list pending and reviewed urgent encounters through
`GET /review-queue`, then mark a queue item as reviewed without changing the
source encounter or triage result.

This is a specification only. It does not define implementation code.

## Goals

- Record every urgent triage encounter in a durable `review_queue` table.
- Include deterministic red-flag escalations in the queue, even when the stored
  triage level is `seek_immediate_care`.
- Expose a clinician endpoint for reading review queue items.
- Provide an endpoint for marking queue items reviewed.
- Keep review workflow state separate from original triage data.

## Out of Scope

- Clinician authentication and authorization.
- Frontend review queue UI.
- Editing or deleting encounters.
- Changing triage decision logic or red-flag matching.
- Notification delivery, paging, or integrations with clinical systems.

## Queue Criteria

A review queue item must be created for a triage encounter when the final
persisted triage result meets either condition:

- `triage_level == "urgent"`
- `triage_level == "seek_immediate_care"`

`seek_immediate_care` covers deterministic red-flag escalations and must be
treated as urgent for queueing purposes.

Queue creation happens after the source encounter is persisted and must refer to
that encounter by ID.

## Data Model

### `review_queue` Table

| Field | Type | Required | Notes |
|---|---:|---:|---|
| `id` | integer primary key | yes | Queue item identifier. |
| `encounter_id` | integer foreign key | yes | References `encounter.id`; unique to prevent duplicate queue items for the same encounter. |
| `created_at` | datetime | yes | Time the queue item was created. |
| `review_status` | string | yes | Allowed values: `pending`, `reviewed`. Defaults to `pending`. |
| `reviewed_at` | datetime nullable | no | Set when `review_status` becomes `reviewed`. |
| `reviewed_by` | string nullable | no | Optional clinician/user identifier when auth exists; may be omitted until auth is implemented. |

### Relationships and Constraints

- `review_queue.encounter_id` must reference an existing encounter.
- `review_queue.encounter_id` must be unique.
- Deleting or changing a review queue row must not delete or mutate the
  associated encounter.
- The source encounter remains the system of record for age, sex, symptoms text,
  triage level, rationale, disclaimer, and creation time.

### Derived Response Fields

`GET /review-queue` should include enough encounter detail for a clinician to
decide what to review without another API call:

- Queue fields: `id`, `encounter_id`, `created_at`, `review_status`,
  `reviewed_at`, `reviewed_by`
- Encounter fields: `encounter_created_at`, `age`, `sex`, `symptoms_text`,
  `triage_level`, `rationale`, `disclaimer`

The response must include `disclaimer` for each item.

## Endpoints

### `GET /review-queue`

Returns a paginated list of urgent review queue items for clinicians.

#### Query Parameters

| Name | Type | Default | Validation | Notes |
|---|---:|---:|---|---|
| `status` | string | `pending` | one of `pending`, `reviewed`, `all` | Filters by review status. |
| `limit` | integer | `20` | `1 <= limit <= 100` | Page size. |
| `offset` | integer | `0` | `offset >= 0` | Page offset. |

#### Sorting

- Default order: `created_at` descending, newest queue items first.
- Sorting is based on the queue item creation time, not review time.

#### Response

Status: `200 OK`

```json
{
  "items": [
    {
      "id": 123,
      "encounter_id": 456,
      "created_at": "2026-06-07T15:04:05Z",
      "review_status": "pending",
      "reviewed_at": null,
      "reviewed_by": null,
      "encounter_created_at": "2026-06-07T15:04:04Z",
      "age": 48,
      "sex": "female",
      "symptoms_text": "synthetic urgent symptom text",
      "triage_level": "urgent",
      "rationale": "Synthetic rationale for urgent clinician review.",
      "disclaimer": "This output is not a medical diagnosis. Always consult a qualified clinician for medical advice."
    }
  ],
  "total": 1
}
```

`total` is the total number of queue items matching the filter, independent of
`limit` and `offset`.

### `PATCH /review-queue/{queue_item_id}/reviewed`

Marks one review queue item as reviewed.

#### Path Parameters

| Name | Type | Notes |
|---|---:|---|
| `queue_item_id` | integer | Existing review queue item ID. |

#### Request Body

```json
{
  "reviewed_by": "clinician-user-id"
}
```

`reviewed_by` is optional until authentication exists. If omitted, the API still
marks the item reviewed and sets `reviewed_at`.

#### Response

Status: `200 OK`

Returns the updated queue item, including its associated encounter fields and
unchanged triage data.

#### Error Cases

- `404 Not Found` when `queue_item_id` does not exist.
- `422 Unprocessable Entity` for invalid path or body values.

#### Idempotency

Calling the endpoint on an already reviewed item should be safe and idempotent:

- Keep `review_status == "reviewed"`.
- Do not change the original encounter.
- Preserve the original `reviewed_at` unless the implementation explicitly
  documents a reason to refresh it.

## Acceptance Criteria

1. Creating a triage encounter with `triage_level == "urgent"` creates exactly
   one `review_queue` row linked to that encounter.
2. Creating a deterministic red-flag encounter with
   `triage_level == "seek_immediate_care"` creates exactly one `review_queue`
   row linked to that encounter.
3. Creating encounters with `triage_level == "self_care"` or
   `triage_level == "see_clinician"` does not create review queue rows.
4. Queue creation is atomic with urgent encounter persistence: the system must
   not persist an urgent encounter without its corresponding queue row.
5. Duplicate queue rows are prevented for the same encounter.
6. `GET /review-queue` returns `pending` items by default, newest first.
7. `GET /review-queue?status=reviewed` returns only reviewed items.
8. `GET /review-queue?status=all` returns pending and reviewed items.
9. Pagination validates `limit` and `offset`, and `total` reflects all matching
   rows before pagination.
10. Every response item includes the safety `disclaimer`.
11. `PATCH /review-queue/{queue_item_id}/reviewed` sets
    `review_status == "reviewed"` and sets `reviewed_at`.
12. Marking an item reviewed never changes the linked encounter's
    `triage_level`, `rationale`, `disclaimer`, `symptoms_text`, or
    `created_at`.
13. Requesting or updating a missing queue item returns `404`.

## Safety

- The system must not lose any urgent encounter. Any triage result with
  `triage_level == "urgent"` or `triage_level == "seek_immediate_care"` must be
  represented in `review_queue`.
- Review status is workflow metadata only. It must never alter the original
  triage record or imply that the clinical risk is resolved.
- The original encounter remains the immutable source of truth for the triage
  output.
- The API must continue returning the existing disclaimer on every surfaced
  triage result.
- The endpoint must not add logs or prints that emit symptoms text, rationale,
  or other patient encounter details.
- Tests and examples must use synthetic data only.
