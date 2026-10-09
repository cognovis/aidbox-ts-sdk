#!/usr/bin/env bash
# Preflight run by the fleet-wide pre-push hook (global core.hooksPath).
# Delegates to the tracked .hooks/pre-push so both routes run the same checks.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
exec .hooks/pre-push "$@"
