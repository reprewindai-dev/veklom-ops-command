# Veklom Windows evidence checks

Status: generated for Windows PowerShell 5.1 or PowerShell 7 on Windows. PowerShell is not installed in the preparation environment, so these scripts have NOT been parsed or executed there. The launcher performs PowerShell parser checks on your machine before running the collectors. The included Node resolver tests were separately exercised locally; that does not establish the PowerShell wrapper runs correctly.

## First run: no repository paths or keys required

Extract this ZIP, open PowerShell in that extracted folder and run:

    .\Run-VeklomChecks.ps1 -Role Earth -DurationSeconds 60

On the other machine:

    .\Run-VeklomChecks.ps1 -Role Mars -DurationSeconds 60

During each capture, use the normal CLI/IDE workflow in another window. These runs do NOT generate test traffic. Start them close together for cross-host comparison; UTC timestamps depend on your clocks and are not proof that clocks are synchronized.

The output goes under your Windows TEMP directory in VeklomEvidence. The scripts print the exact evidence ZIP paths. Return the ZIP from each machine, not screenshots alone. Addresses, ports, process names and SDK source are private operational information: inspect archives before sharing. No API keys, process command lines, environment dumps or user names are intentionally recorded.

If script execution is blocked by your security policy, do not disable a machine-wide policy just for this bundle. Use your normal approved script-running process. No automatic elevation, software installation, remote execution, deployment or reboot occurs. Socket-read permission failures are recorded as errors, not successful empty captures; run from an authorized elevated terminal only if needed.

## CLI/IDE workspace-binding red/green check

    .\Test-VeklomIdeBinding.ps1 -SdkRepo (Read-Host 'Full path to veklom-sdk checkout') -CheckInstalledCompiler

This source-specific check expects src/workspace.ts Git blob 8a67d894a10564fe5999b6aa2e447b5ac79ed9ac after line-ending normalization. It makes temporary baseline and patched copies in the evidence directory, applies only the exact-root fallback removal to the copy, and runs the identical 14 Node tests on both. Expected outcome: baseline 4 failures; patched 14 passes. SOURCE_REVISION_MISMATCH means send the revision report; the script will not guess a new patch.

The original checkout is not patched, installed, built or committed. If TypeScript is already installed locally, -CheckInstalledCompiler runs the ORIGINAL checkout's compiler with noEmit and incremental=false. Missing dependencies are reported; npm install is never invoked. Compiler success on the original checkout is not compilation proof for the patched copy. Native execution is limited to the installed Node binary. A timed-out test/compiler child is terminated and reported. No existing service is killed.

The Node tests execute the exact resolver body after removing its reviewed TypeScript function signature. A small VS Code API fixture is injected. These are isolated resolver tests, not installed extension-host integration tests, symlink containment tests, or independent acceptance. They do not prove current authority, replay finality, state readback or ledger persistence.

You can combine collection and the optional IDE check:

    .\Run-VeklomChecks.ps1 -Role Earth -RunIdeChecks -SdkRepo (Read-Host 'Full path to veklom-sdk checkout') -CheckInstalledCompiler

## Optional authenticated ledger readback: GET only

    .\Test-VeklomLedgerReadback.ps1 -BaseUri (Read-Host 'Actual configured ledger origin, e.g. https://your-ledger-host/') -EventId (Read-Host 'Real event ID from your receipt') -ExpectedEventHash (Read-Host 'Expected event hash from that receipt') -PromptForApiKey

Alternatively supply an existing process environment variable VEKLOM_PGL_API_KEY; its value is not written into reports. Do NOT paste a key in chat or put it directly on the command line. The masked key input does not save the credential; network requests necessarily hold it in process memory. Do not enable a transcript or debug trace for credential handling.

The endpoint paths are the existing contracts:
- GET /api/v1/ledger/events/{event_id}
- With -AgentId, separately GET /api/v1/ledger/agents/{agent_id}/verify

The origin must not include an embedded credential, path, query or fragment. HTTPS is required outside loopback unless you explicitly supply -AllowInsecureHttp on your trusted test network. Redirects are refused and server certificate checks are not bypassed. Only GET requests are sent; the service may still update normal access/audit metadata.

The report filters the response to selected identity/hash/status fields, not arbitrary payload details. MATCH is a local comparison result, not an invented server response code. A separately valid server chain report does NOT establish event membership, independent signature verification, a target mutation, or production finality. Missing credentials, endpoint failures and malformed data do not turn into Verified.

## Socket evidence scope

Collect-VeklomSockets.ps1 samples current connections whose local OR remote port matches 8400, 8020, 8040, 8050, 8060, 9015 or 9016. The role labels are operator labels, not detected host identities. It records UTC/elapsed times, addresses, ports, TCP states, owning PIDs, and available process memory/CPU/handle snapshots. A row limit and duration limit bound collection. No FIN/RST packet counts, application multiplexing counts, RF shutdown, packet delivery, durable commits, memory-leak freedom or forbidden-mutation counts are inferred.

No SO_LINGER changes, forced resets, radio changes, authority calls, speculative commits or stress loads are performed. Reproducing transport chaos requires a separately reviewed, isolated experiment; the passive collector is not such an experiment.

## Existing telemetry remains unverified

The supplied authority-port list enumerates 11 distinct remote ports (51748, 51750, 51752, 51781 through 51787, 56288), not 15. That may be an incomplete list or a count mismatch; it is not proof either way. Snapshot captures cannot retrospectively reproduce the reported 3-million-request run. Such a claim additionally requires raw request/decision/transport records plus authoritative target-state evidence.

## Integrity and completion

The launcher checks shipped file hashes and parses every PowerShell script/module before collecting. Every completed run includes RUN.json, SUMMARY.json and checksums.json, then a ZIP. A RUNNING marker without a completed manifest is partial evidence. Checksums detect byte changes only relative to their manifest; they are not signatures, tamper-proof storage or independent verification. Compiler/source and capture errors must remain visible.

No GitHub write, merge or deployment is part of these scripts. The earlier proposed SDK commit is still awaiting an explicit approval; this bundle does not silently apply it.
