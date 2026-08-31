# Quickstart

Connect an MCP client to GateCore and call the public tools.

**Endpoint:** `https://mcp.gatecoreai.com/mcp`
**Transport:** streamable HTTP

## Two things worth knowing before anything works

**1. Send the Accept header.**

```
Accept: application/json, text/event-stream
```

The MCP streamable HTTP spec calls for this header, and the endpoint accepts a lenient range
of Accept values (including none at all) rather than rejecting requests that omit it. Send it
anyway: it is the spec-conformant, forward-compatible choice, and any conformant MCP client
library sends it for you without being asked.

**2. Complete the `initialize` handshake first.** This one *is* enforced.

The server issues a session on `initialize` and returns it in the `mcp-session-id` response
header. Send that value back as the `MCP-Session-Id` header on every later request. Calling
`tools/list` or `tools/call` without a session returns **400 Bad Request** with
`"Missing session ID"`. This is also transport, not authentication.

Responses arrive as Server-Sent Events, so the JSON body is on a `data: ` line.

Any conformant MCP client library performs this handshake for you. The raw examples below
exist so the failure modes are recognizable when a hand-rolled client hits them.

## The handshake, with curl

```bash
# 1. initialize, and capture the session id from the response headers
curl -sD headers.txt -X POST https://mcp.gatecoreai.com/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{
        "protocolVersion":"2025-06-18","capabilities":{},
        "clientInfo":{"name":"my-agent","version":"0.1.0"}}}'

SESSION=$(grep -i '^mcp-session-id:' headers.txt | tr -d '\r' | awk '{print $2}')

# 2. tell the server you are initialized
curl -s -X POST https://mcp.gatecoreai.com/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H "MCP-Session-Id: $SESSION" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'

# 3. list the tools
curl -s -X POST https://mcp.gatecoreai.com/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H "MCP-Session-Id: $SESSION" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'
```

Step 2 returns `202 Accepted` with no body. That is correct.

A ready-made version of this script is in
[examples/discover.sh](examples/discover.sh), and a stdlib-only Python client is in
[examples/discover.py](examples/discover.py).

## Public tools

| Tool | Arguments | Key required |
| --- | --- | --- |
| `discover_listings` | `query`, `tags`, `max_price_cents`, `min_trust` (all optional) | No |
| `get_listing` | `listing_id` (required) | No |
| `procure` | `listing_id`, `requester_agent_id`, `requester_trust` (required); `scopes`, `max_price_cents` (optional) | Yes |
| `list_procurements` | none | Yes |
| `submit_lead` | `listing_id`, `lead` (required) | Yes |

## Discovery is anonymous

`discover_listings` and `get_listing` need no key and no account. Discovery returns
published listings only.

```bash
curl -s -X POST https://mcp.gatecoreai.com/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H "MCP-Session-Id: $SESSION" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{
        "name":"discover_listings","arguments":{"max_price_cents":500}}}'
```

Take a `listing_id` from that result and fetch the full contract:

```bash
curl -s -X POST https://mcp.gatecoreai.com/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H "MCP-Session-Id: $SESSION" \
  -d '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{
        "name":"get_listing","arguments":{"listing_id":"listing:tool-sodzilla-lead-quote"}}}'
```

The returned contract carries the price in cents, the required scopes, the minimum trust
threshold, the target, and the data classification, so an agent can decide whether to
proceed without a human reading the page.

## Procurement and lead submission need a key

`procure`, `list_procurements`, and `submit_lead` require a GateCore MCP access key, which
carries a `gcmk_` prefix. Send it as a bearer token:

```
Authorization: Bearer gcmk_<your-key>
```

Without a key, these three tools fail closed. The response is a normal JSON-RPC tool
result with `isError: true` and the message `MCP key required: register via GateCore`. Note
that this is a tool-level refusal, not an HTTP status code, so a client that only checks
for 200 against 401 will miss it.

Identity and tenant scope come from the key, not from tool-call arguments. That is
deliberate: an agent cannot claim to be someone else by passing a different
`requester_agent_id`.

### `submit_lead` specifically

`submit_lead` delivers a consented consumer lead to a listing that accepts them. Three
things are true of it and worth stating plainly:

- **Anonymous lead submissions are refused as unverified.** A lead with no credentialed
  agent behind it is not a verified lead, and GateCore will not deliver it. This is a
  product rule about lead quality, not only an access control.
- **The submitting agent must already hold the end user's explicit consent** to share
  their contact details.
- **The required payload fields are stated on the listing's own contract.** Fetch the
  listing with `get_listing` and read the contract rather than guessing at the shape.

Lead-listing pages on the public marketplace also carry a `leadSubmission` JSON-LD object
with the endpoint, the required key class, the procurement arguments, the lead payload
schema, and the rejection conditions, so an agent can learn the whole flow from the page.

## Getting a key

Get a GateCore MCP access key self-serve at
[app.gatecoreai.com/developer/portal](https://app.gatecoreai.com/developer/portal). For
anything else, contact [hello@gatecoreai.com](mailto:hello@gatecoreai.com).

## Troubleshooting

| Symptom | Cause |
| --- | --- |
| HTTP 400, `Missing session ID` | No `initialize` handshake, or the `MCP-Session-Id` header was not sent back. |
| Empty-looking response body | The response is Server-Sent Events. Read the JSON from the `data: ` line. |
| `isError: true`, `MCP key required` | The tool needs a `gcmk_` access key. |
