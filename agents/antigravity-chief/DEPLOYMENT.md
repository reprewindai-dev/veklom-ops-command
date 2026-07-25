# Deployment - antigravity-chief

antigravity-chief coordinates deployments but does not execute them directly.
Deployments flow through: antigravity-chief -> release-chief -> platform-chief

## Exception: Emergency
If release-chief and platform-chief are both unavailable:
antigravity-chief may SSH to Hetzner and run deploy_all.sh directly.
This is an emergency-only action.
