#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
exec uv run mbf run --config examples/config_eqe_health.yaml
