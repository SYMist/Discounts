#!/usr/bin/env bash
set -euo pipefail

# Replace GA_MEASUREMENT_ID_PLACEHOLDER across all shipped HTML files.
# Requires env var GA_MEASUREMENT_ID to be set (e.g., G-XXXXXXXXXX).

if [[ -z "${GA_MEASUREMENT_ID:-}" ]]; then
  echo "[replace_ga] Error: GA_MEASUREMENT_ID is not set." >&2
  exit 1
fi

echo "[replace_ga] Replacing placeholders with GA_MEASUREMENT_ID=${GA_MEASUREMENT_ID}"

# apps/web/public (all html)
find apps/web/public -type f -name '*.html' -print0 | \
  xargs -0 sed -i.bak "s|GA_MEASUREMENT_ID_PLACEHOLDER|${GA_MEASUREMENT_ID}|g"

# crawler templates (all html)
find apps/crawler/templates -type f -name '*.html' -print0 | \
  xargs -0 sed -i.bak "s|GA_MEASUREMENT_ID_PLACEHOLDER|${GA_MEASUREMENT_ID}|g"

# cleanup backups
find apps/web/public apps/crawler/templates -name '*.bak' -delete

echo "[replace_ga] Done."

