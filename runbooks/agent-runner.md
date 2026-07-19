# Veklom Agent Runner

The runner is the execution layer between the founder inbox and department reports. It reads the newest queued instruction, sends each department a constrained prompt containing its own doctrine and roster, validates the returned JSON, writes `reports/departments/<team>.jsonl`, updates Mission state, and writes a run record under `reports/agent-runs/`.

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
