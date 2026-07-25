# Deployment - truth-chief

truth-chief does NOT deploy production services.
truth-chief VERIFIES that deployment was successful.

After release-chief deploys:
1. truth-chief runs the full verification sweep
2. If all checks pass: issue sign-off
3. If any check fails: signal release-chief to halt and investigate
