# Veklom Agent Runner

The runner is the parent/child execution layer between the founder inbox and department reports. The Command Desk parent reads the newest queued instruction as a trigger, then loads the canonical toolbox meeting from `reports/toolbox-meetings/<mission_id>.json` and spawns one isolated child worker for each department. Each child receives its own doctrine, roster, mission, and cAPI admission context, then returns validated JSON to `reports/departments/<team>.jsonl`. The parent updates Mission state and writes a run record under `reports/agent-runs/`.

For continuous operation, run `scripts/start-agent-watch.ps1` from PowerShell or `scripts/start-agent-watch.cmd`. The watch daemon observes the declared Veklom ops scope and triggers the governed runner when the founder inbox changes. It does not grant production tools.

## Configure

PowerShell:

```powershell
$env:VEKLOM_AGENT_API_KEY = "<your key>"
$env:VEKLOM_AGENT_MODEL = "<approved model>"
```

Optional provider override: `VEKLOM_AGENT_BASE_URL`. The default is the OpenAI-compatible `/v1/chat/completions` endpoint. The runner has no shell, SSH, deployment, database, secret, or production tools.

## Run

```powershell
.
scripts\run-agent-mission.ps1
```

Use `VEKLOM_AGENT_COMMIT=true` only when you want the generated reports committed. Push remains an explicit `git push origin main` step.
