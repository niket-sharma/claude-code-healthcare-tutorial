# PHI-shaped patterns to flag

- `logger.*(.*symptoms_text.*` combined with any id/name/email field
- `print(.*encounter` or `print(.*intake`
- regex for keys: sk-[A-Za-z0-9]{20,}
- f-strings interpolating both a patient identifier and free-text symptoms
- exception handlers that `repr()` or `str()` a full request body into logs

# Safe alternatives to recommend
- Log an encounter_id only, never the content
- Redact free text before logging
- Keep secrets exclusively in environment/config