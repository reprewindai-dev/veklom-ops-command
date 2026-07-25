# Tests - release-chief

## SHA Verification Test
# SSH and compare deployed SHA vs GitHub HEAD
# git -C /data/coolify/applications/<app> rev-parse HEAD
# vs: gh api repos/reprewindai-dev/<repo>/branches/main | jq '.commit.sha'

## deploy_all.sh Syntax Test
bash -n C:\Users\antho\.windsurf\deploy_all.sh

## Post-Deploy Health Suite
curl https://capi.veklom.com/health
curl https://pgl.veklom.com/health
curl https://cappo.veklom.com/health
curl https://api.veklom.com/health
curl https://abide.veklom.com/health
curl https://terminal.veklom.com/
