# Server Role Map

| Server | Role | Guardrail |
|---|---|---|
| Coolify controller (localhost) | current production/control host | no direct mutation from watcher |
| veklom-edge-us-east | NA probe/failover candidate | probe first |
| veklom-edge-eu-central | EU probe/compliance/PGL export | no premature writes |
| veklom-edge-eu-north2 | build-agent/staging/Jean/Poltergeist lane | build only |
| veklom-edge-ap-southeast | APAC probe/VNP scoring | probe first |
| stupid-seahorse-n7gx1qmxtb1ulrbmb09rtyt0 | unusable/quarantined | do not deploy |
