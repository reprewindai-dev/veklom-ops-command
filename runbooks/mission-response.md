# Mission Response Contract

Each department reports one JSON object per line to `reports/departments/<department>.jsonl`:

```json
{"mission_id":"mission-001","department":"production-truth","captain":"...","mission_understanding":"...","owned_systems":[],"risks":[],"forbidden_actions":[],"definition_of_done":[],"handoff_to":"...","status":"aligned|blocked|needs_clarification","reported_at":"..."}
```

Do not fabricate replies. The panel marks departments as awaiting response until a real response file exists.
