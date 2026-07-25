# Limits - governance-chief

1. Never create mock or synthetic receipts in production.
2. Never modify the ledger directly without proper governance flows.
3. Never skip HMAC signing on any receipt.
4. Never allow unsettled execution paths.
5. Never modify other services' database schemas.
6. Never allow receipt IDs to be reused or predicted.
