#!/usr/bin/env bash
# Read-only testnet deployment drift check (issue #236).
#
# Fetches the bytecode currently installed for the contract recorded in
# deployments/testnet.json and compares its sha256 with the recorded
# wasmHash. Never deploys, installs, invokes, or edits the record.
#
# Exit codes: 0 = match, 1 = drift (hash mismatch), 2 = fetch/RPC failure
# or unusable record (not evidence of drift).
set -euo pipefail

RECORD="${RECORD:-deployments/testnet.json}"
NETWORK="${NETWORK:-testnet}"

contract_id="$(jq -er '.WillContract' "$RECORD")" || { echo "::error::cannot read contract id from $RECORD"; exit 2; }
recorded="$(jq -er '.wasmHash' "$RECORD")" || { echo "::error::cannot read wasmHash from $RECORD"; exit 2; }
if [[ ! "$recorded" =~ ^[0-9a-f]{64}$ ]] || [[ "$recorded" =~ ^0+$ ]]; then
  echo "::error::$RECORD has a placeholder or malformed wasmHash ($recorded); record a real deployment first"
  exit 2
fi

tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
if ! stellar contract fetch --id "$contract_id" --network "$NETWORK" --out-file "$tmp/live.wasm"; then
  echo "::error::RPC/fetch failure for $contract_id on $NETWORK — drift NOT demonstrated"
  exit 2
fi

live="$(sha256sum "$tmp/live.wasm" | cut -d' ' -f1)"
if [[ "$live" != "$recorded" ]]; then
  echo "::error::DRIFT: $contract_id on $NETWORK runs $live, $RECORD records $recorded"
  exit 1
fi
echo "OK: $contract_id on $NETWORK matches recorded wasmHash $recorded"
