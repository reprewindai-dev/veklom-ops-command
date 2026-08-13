# Cloudflare Infrastructure Provisioning Script

Write-Host "Provisioning Cloudflare Infrastructure for VEKLOM..."

# 1. KV Namespaces
Write-Host "Creating KV Namespaces..."
wrangler kv:namespace create "VEKLOM_IMMUTABLE_CACHE"
wrangler kv:namespace create "VEKLOM_IMMUTABLE_CACHE" --env canary

# 2. Hyperdrive
# Note: You must replace the connection strings with the actual connection strings to your Server 0 PostgreSQL database
Write-Host "Creating Hyperdrive Configurations..."
Write-Host "Please ensure you have your PostgreSQL connection string ready. (e.g. postgresql://user:password@tunnel-host:5432/db)"
# wrangler hyperdrive create veklom-db-cacheable --connection-string="<YOUR_CONNECTION_STRING>"
# wrangler hyperdrive create veklom-db-fresh --connection-string="<YOUR_CONNECTION_STRING>" --caching-disabled
# wrangler hyperdrive create veklom-db-cacheable-canary --connection-string="<YOUR_CONNECTION_STRING>"
# wrangler hyperdrive create veklom-db-fresh-canary --connection-string="<YOUR_CONNECTION_STRING>" --caching-disabled

# 3. Queues
Write-Host "Creating Queues..."
wrangler queues create veklom-async-refinery
wrangler queues create veklom-async-refinery-canary

Write-Host ""
Write-Host "Please update wrangler.toml and wrangler-connector.toml with the IDs output by the commands above."
Write-Host "Once updated, you can deploy using:"
Write-Host "wrangler deploy -c wrangler-connector.toml --env canary"
Write-Host "wrangler deploy -c wrangler.toml --env canary"
Write-Host "wrangler deploy -c wrangler-connector.toml --env production"
Write-Host "wrangler deploy -c wrangler.toml --env production"
