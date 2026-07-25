# Tests - devex-chief

## Documentation Accuracy Test
# Each README instruction must be runnable from scratch
# Test: follow the getting started guide, verify it works

## SDK Example Test
# All SDK code examples must run successfully against live endpoints
# cd veklom-sdk && npm test

## API Documentation Completeness Test
# Every public endpoint must have a documentation entry
# Check: curl https://cappo.veklom.com/openapi.json | jq '.paths | keys'
# Verify each key has a corresponding docs entry
