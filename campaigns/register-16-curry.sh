#!/bin/bash
# Registers the 16 Curry Crescent campaign on the self-hosted dashboard.
# Run on the server: cd /opt/realtor-bot && bash campaigns/register-16-curry.sh
# (The dashboard store already exists there, so seed.json changes alone
# will not appear — this registers through the API instead.)
set -e
cd "$(dirname "$0")/.."
KEY=$(grep ^DASHBOARD_KEY= .env | cut -d= -f2)
[ -n "$KEY" ] || { echo "DASHBOARD_KEY not set in .env"; exit 1; }

python3 - <<'EOF' > /tmp/curry-meta.json
import json
seed = json.load(open("dashboard/seed.json"))
c = seed["campaigns"]["16-curry"]
meta = {k: c[k] for k in ("name", "subtitle", "status", "playbook", "targets", "config", "rules")}
print(json.dumps(meta))
EOF

curl -sS -X PUT localhost:8080/api/campaigns/16-curry \
  -H "Content-Type: application/json" -H "X-Dashboard-Key: $KEY" \
  --data @/tmp/curry-meta.json
echo
curl -sS -X POST localhost:8080/api/campaigns/16-curry/log \
  -H "Content-Type: application/json" -H "X-Dashboard-Key: $KEY" \
  -d '{"date":"2026-07-22","title":"Campaign created, mirroring Buttonleaf","entry":"Same $15/day structure and curiosity strategy. Property hooks: 4-car garage, walk-up basement in-law suite potential, $60K waterproofing and new mechanicals already done."}'
echo
echo "Registered. Check http://87.99.139.222:8080/"
