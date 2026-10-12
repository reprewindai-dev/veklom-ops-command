# Tests - release-chief

## SHA Verification Test
# On the owned Docker host, compare the SHA the running service was built from
# vs: gh api repos/reprewindai-dev/<repo>/branches/main | jq '.commit.sha'

## Deploy Procedure Check
# Confirm the release proof records the observed owned host, compose project, and SHA per runbooks/release-deploy.md

## Post-Deploy Health Suite
curl https://capi.veklom.com/health
curl https://pgl.veklom.com/health
curl https://cappo.veklom.com/health
curl https://api.veklom.com/health
curl https://abide.veklom.com/health
curl https://terminal.veklom.com/
