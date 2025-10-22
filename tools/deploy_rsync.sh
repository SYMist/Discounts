#!/usr/bin/env bash
set -euo pipefail

# Deploy apps/web/public to remote docroot via rsync.
# Usage:
#   export DEPLOY_HOST=your.host
#   export DEPLOY_USER=youruser
#   export DEPLOY_PATH=/var/www/discounts/apps/web/public
#   ./tools/deploy_rsync.sh

if [[ -z "${DEPLOY_HOST:-}" || -z "${DEPLOY_USER:-}" || -z "${DEPLOY_PATH:-}" ]]; then
  echo "Please set DEPLOY_HOST, DEPLOY_USER, DEPLOY_PATH env vars" >&2
  exit 1
fi

SRC_DIR="$(cd "$(dirname "$0")/.." && pwd)/apps/web/public/"

rsync -avz --delete \
  --exclude ".DS_Store" \
  "$SRC_DIR" "${DEPLOY_USER}@${DEPLOY_HOST}:${DEPLOY_PATH}/"

echo "✅ Deployed to ${DEPLOY_USER}@${DEPLOY_HOST}:${DEPLOY_PATH}/"

