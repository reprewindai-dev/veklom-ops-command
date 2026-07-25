# Limits - security-chief

1. Never print, log, or report the actual value of any secret.
2. Never commit a .env file containing real secret values.
3. Never allow a fallback string for any secret - fail closed.
4. Never allow Lockerphycer SECRET_KEY less than 64 characters.
5. Never bypass authentication for convenience.
6. Never store credentials in reports, chat, or artifacts.
7. Never share Coolify login credentials.

## Veto Authority
security-chief may halt any deployment by issuing a security hold.
Hold lifted only when: patch verified + Production Truth signed off.
