#!/usr/bin/env bash
# Discover GateCore marketplace listings with curl. No key or account required.
#
#   ./discover.sh                 # list published listings
#   ./discover.sh <listing_id>    # fetch one listing and its contract
#
# Requires: curl. jq is optional and only used to pretty-print.
set -euo pipefail

ENDPOINT="https://mcp.gatecoreai.com/mcp"
# Both parts of this Accept header are required. Without it the endpoint
# returns 406, which is a transport error and not an auth error.
ACCEPT="application/json, text/event-stream"
HEADERS=$(mktemp)
trap 'rm -f "$HEADERS"' EXIT

# 1. initialize, and capture the session id the server issues
curl -sS -D "$HEADERS" -o /dev/null -X POST "$ENDPOINT" \
  -H 'Content-Type: application/json' \
  -H "Accept: $ACCEPT" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{
        "protocolVersion":"2025-06-18","capabilities":{},
        "clientInfo":{"name":"gatecore-example","version":"1.0.0"}}}'

SESSION=$(grep -i '^mcp-session-id:' "$HEADERS" | tr -d '\r' | awk '{print $2}')
if [ -z "${SESSION:-}" ]; then
  echo "no session id returned by initialize" >&2
  exit 1
fi

# 2. tell the server the handshake is complete (returns 202, no body)
curl -sS -o /dev/null -X POST "$ENDPOINT" \
  -H 'Content-Type: application/json' \
  -H "Accept: $ACCEPT" \
  -H "MCP-Session-Id: $SESSION" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'

# 3. call a tool
if [ $# -ge 1 ]; then
  PARAMS=$(printf '{"name":"get_listing","arguments":{"listing_id":"%s"}}' "$1")
else
  PARAMS='{"name":"discover_listings","arguments":{}}'
fi

# Replies arrive as Server-Sent Events, so strip the "data: " prefix.
curl -sS -X POST "$ENDPOINT" \
  -H 'Content-Type: application/json' \
  -H "Accept: $ACCEPT" \
  -H "MCP-Session-Id: $SESSION" \
  -d "{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/call\",\"params\":$PARAMS}" \
  | sed -n 's/^data: //p' \
  | { command -v jq >/dev/null 2>&1 && jq . || cat; }
