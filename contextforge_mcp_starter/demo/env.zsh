# Source this from contextforge_mcp_starter. These settings contain no credentials.
if [[ ! -f demo/source_contract.json || ! -x .venv/bin/python ]]; then
  print -u2 'Run cd /Applications/Projects/Hackmidwest/contextforge_mcp_starter before sourcing demo/env.zsh'
  return 1
fi
export AWS_PROFILE="${AWS_PROFILE:-contextforge}"
export AWS_REGION="${AWS_REGION:-us-east-2}"
export STRANDS_MODEL_ID="${STRANDS_MODEL_ID:-us.amazon.nova-micro-v1:0}"
export CONTEXTFORGE_SOURCE_URL='http://127.0.0.1:8001'
export CONTEXTFORGE_ALLOWED_SOURCE_HOSTS='127.0.0.1'
export CONTEXTFORGE_CONTRACT_PATH="$PWD/demo/source_contract.json"
export CONTEXTFORGE_VALIDATION_CASES_PATH="$PWD/demo/validation_cases.json"
export CONTEXTFORGE_DB="$PWD/state/capabilities.sqlite3"
