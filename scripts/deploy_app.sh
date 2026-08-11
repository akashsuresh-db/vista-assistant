#!/usr/bin/env bash
# Deploy the Vista Assistant as a Databricks App and grant the service principal
# everything it needs.
#
# Usage: ./scripts/deploy_app.sh <supervisor_endpoint_name>
#
# The SP grants matter: an Agent Bricks Supervisor calls its sub-agents AS THE CALLER,
# so the App's SP needs CAN_QUERY on the supervisor endpoint AND on the Knowledge
# Assistant endpoint, plus CAN_RUN on the Genie space. Missing any one of them shows up
# as an opaque failure inside the agent rather than a clear permission error.
set -euo pipefail

# All configuration read from config.yaml via config.py
# This script extracts values and uses them for deployment
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Read configuration from config.yaml
PROFILE=$(python3 - <<'PYCFG'
import sys; sys.path.insert(0, '.'); from scripts.config import CFG; print(CFG.profile)
PYCFG
)
APP_NAME=$(python3 - <<'PYCFG'
import sys; sys.path.insert(0, '.'); from scripts.config import CFG; print(CFG.app_name)
PYCFG
)
KA_ENDPOINT=$(python3 - <<'PYCFG'
import sys; sys.path.insert(0, '.'); from scripts.config import CFG; print(CFG.ka_endpoint)
PYCFG
)
GENIE_SPACE=$(python3 - <<'PYCFG'
import sys; sys.path.insert(0, '.'); from scripts.config import CFG; print(CFG.genie_space_id)
PYCFG
)
WAREHOUSE=$(python3 - <<'PYCFG'
import sys; sys.path.insert(0, '.'); from scripts.config import CFG; print(CFG.warehouse_id)
PYCFG
)
CATALOG=$(python3 - <<'PYCFG'
import sys; sys.path.insert(0, '.'); from scripts.config import CFG; print(CFG.catalog)
PYCFG
)
SCHEMA=$(python3 - <<'PYCFG'
import sys; sys.path.insert(0, '.'); from scripts.config import CFG; print(CFG.schema)
PYCFG
)
VOLUME=$(python3 - <<'PYCFG'
import sys; sys.path.insert(0, '.'); from scripts.config import CFG; print(CFG.volume)
PYCFG
)

SUPERVISOR="${1:-}"
if [[ -z "$SUPERVISOR" ]]; then
  echo "usage: $0 <supervisor_endpoint_name>   (e.g. mas-1a2b3c4d-endpoint)" >&2
  exit 1
fi

echo "==> 1/6 wiring app.yaml to $SUPERVISOR"
python - "$SUPERVISOR" <<'PY'
import pathlib, re, sys
ep = sys.argv[1]
p = pathlib.Path("app/app.yaml")
s = p.read_text()
s = re.sub(r'(- name: SUPERVISOR_ENDPOINT\n    value: ")[^"]*(")', rf'\g<1>{ep}\g<2>', s)
p.write_text(s)
print("   app.yaml ->", ep)
PY

echo "==> 2/6 creating the app (ok if it already exists)"
databricks apps create "$APP_NAME" -p "$PROFILE" 2>/dev/null \
  || echo "   app already exists"

SP=$(databricks apps get "$APP_NAME" -p "$PROFILE" -o json \
     | python -c "import json,sys; print(json.load(sys.stdin)['service_principal_client_id'])")
SP_ID=$(databricks apps get "$APP_NAME" -p "$PROFILE" -o json \
     | python -c "import json,sys; d=json.load(sys.stdin); print(d.get('service_principal_id',''))")
echo "   service principal: $SP"

echo "==> 3/6 granting Unity Catalog + warehouse access"
python scripts/run_sql.py -c "GRANT USE CATALOG ON CATALOG ${CATALOG} TO \`${SP}\`" || true
python scripts/run_sql.py -c "GRANT USE SCHEMA ON SCHEMA ${CATALOG}.${SCHEMA} TO \`${SP}\`" || true
python scripts/run_sql.py -c "GRANT SELECT ON SCHEMA ${CATALOG}.${SCHEMA} TO \`${SP}\`" || true
python scripts/run_sql.py -c "GRANT READ VOLUME ON VOLUME ${CATALOG}.${SCHEMA}.${VOLUME} TO \`${SP}\`" || true

databricks warehouses set-permissions "$WAREHOUSE" -p "$PROFILE" --json "{
  \"access_control_list\": [{\"service_principal_name\": \"${SP}\", \"permission_level\": \"CAN_USE\"}]
}" >/dev/null && echo "   warehouse CAN_USE granted"

echo "==> 4/6 checking endpoint + granting Genie access"
# Agent Bricks owns the endpoints it creates, so the workspace user running this script
# usually does NOT hold Manage on them and cannot grant CAN_QUERY. In practice the App SP
# can already invoke them, so we only VERIFY reachability and warn rather than fail.
for ep in "$SUPERVISOR" "$KA_ENDPOINT"; do
  eid=$(databricks serving-endpoints get "$ep" -p "$PROFILE" -o json \
        | python -c "import json,sys; print(json.load(sys.stdin)['id'])" 2>/dev/null || true)
  if [[ -z "$eid" ]]; then
    echo "   WARNING: cannot read $ep - check the name" >&2
    continue
  fi
  if databricks api put "/api/2.0/permissions/serving-endpoints/${eid}" -p "$PROFILE" --json "{
      \"access_control_list\": [{\"service_principal_name\": \"${SP}\", \"permission_level\": \"CAN_QUERY\"}]
    }" >/dev/null 2>&1; then
    echo "   CAN_QUERY granted on $ep"
  else
    echo "   $ep: no Manage permission to grant explicitly (normal for Agent Bricks)."
    echo "     -> if the app returns a permission error, ask the endpoint owner for"
    echo "        CAN_QUERY for service principal ${SP}"
  fi
done

databricks api put "/api/2.0/permissions/genie/${GENIE_SPACE}" -p "$PROFILE" --json "{
  \"access_control_list\": [{\"service_principal_name\": \"${SP}\", \"permission_level\": \"CAN_RUN\"}]
}" >/dev/null 2>&1 && echo "   CAN_RUN on the Genie space" \
  || echo "   NOTE: grant CAN_RUN on the Genie space in the UI if the app cannot query data"

echo "==> 5/6 uploading source"
TARGET="/Workspace/Users/$(databricks current-user me -p "$PROFILE" -o json \
        | python -c "import json,sys; print(json.load(sys.stdin)['userName'])")/${APP_NAME}"
databricks workspace mkdirs "$TARGET" -p "$PROFILE" 2>/dev/null || true
databricks sync "$ROOT/app" "$TARGET" -p "$PROFILE" --full

echo "==> 6/6 deploying"
databricks apps deploy "$APP_NAME" -p "$PROFILE" --source-code-path "$TARGET"

URL=$(databricks apps get "$APP_NAME" -p "$PROFILE" -o json \
      | python -c "import json,sys; print(json.load(sys.stdin).get('url',''))")
echo
echo "deployed: $URL"
echo "check:    curl -s $URL/api/health"
