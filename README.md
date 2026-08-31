# GateCore

GateCore is the governed transaction layer for AI agents. Every agent request is
identity-verified, policy-checked, priced, settled, and receipted on a tamper-evident
ledger before it touches tools, data, or money.

This repository is GateCore's public integration surface: the MCP server manifest, a
quickstart, runnable client examples, and the agent-facing capability file. It is the
canonical reference for the `com.gatecoreai/marketplace` entry in the official MCP registry.

## What you can do today

Point any MCP client at `https://mcp.gatecoreai.com/mcp` and, with no key and no account:

- **Discover governed capabilities.** `discover_listings` returns published marketplace
  listings with machine-readable price, required scopes, and minimum trust terms attached.
- **Read the contract before you commit.** `get_listing` returns one listing and its
  machine-enforceable contract: price, required scopes, minimum trust, target, and data
  classification. Your agent can evaluate the terms programmatically instead of parsing
  marketing copy.

With a GateCore MCP access key (`gcmk_` prefix), an agent can also:

- **Request a governed procurement decision.** `procure` returns PROCURE, REVIEW, or DENY.
  An eligible decision carries gateway delegation metadata, and execution happens through
  GateCore's signed gateway API.
- **Read its own audit trail.** `list_procurements` returns the procurement decisions
  visible to the credential's tenant.
- **Submit a consented lead.** `submit_lead` delivers a qualified consumer lead to a
  listing that accepts them.

[QUICKSTART.md](QUICKSTART.md) has the exact handshake and copy-pasteable calls.
[examples/](examples/) has short, dependency-light clients for discovery and listing fetch.

## Why terms are machine-readable

An agent that wants to buy something on the open web has to read a human sales page, guess
at the price, guess at the scope of what it is allowed to do with the result, and take the
seller's word for quality. GateCore replaces all three guesses with structured fields on
the listing:

- **Price** is stated in cents on the contract, so an agent can filter by budget before it
  ever asks to transact.
- **Scope** is the explicit set of permissions the capability requires, so an agent can
  check the request against its own policy instead of discovering the mismatch after the
  fact.
- **Trust** is a minimum threshold expressed on the contract. Trust on GateCore is earned
  from verified outcomes. It cannot be asserted by the seller or purchased.

Because those terms are attached to the listing rather than to a sales page, the decision
to transact is one an agent can make on its own and a human can audit afterward.

## Receipts and the audit trail

Every governed decision produces a signed receipt that binds the request, the policy
decision, and the settlement together. Receipts are Ed25519-signed and independently
verifiable: GateCore publishes the receipt signing keys at
`https://api.gatecoreai.com/v1/receipts/keys`, and a client-side verifier at
[gatecoreai.com/verify](https://gatecoreai.com/verify) recomputes the canonical
bytes and checks the signature entirely in the browser. Verification requires no account
and no call back to GateCore, so a receipt stands as evidence to a counterparty who does
not trust us.

That is the point of the design. The decision is bound to the evidence, so "what did the
agent do, under whose authority, at what price, and on what terms" has one answer that
survives the session.

## Public endpoints

| Purpose | URL |
| --- | --- |
| MCP endpoint (streamable HTTP) | `https://mcp.gatecoreai.com/mcp` |
| MCP manifest | `https://mcp.gatecoreai.com/.well-known/mcp.json` |
| Agent capability file | `https://gatecoreai.com/llms.txt` |
| Public marketplace | `https://gatecoreai.com/marketplace/` |
| Receipt verifier | `https://gatecoreai.com/verify` |
| Receipt signing keys | `https://api.gatecoreai.com/v1/receipts/keys` |

## Registry entry

GateCore is listed on the official Model Context Protocol registry as
`com.gatecoreai/marketplace`. [server.json](server.json) in this repository is that
manifest.

## Access keys

Discovery is open. Procurement, procurement history, and lead submission require a
GateCore-issued MCP access key so that agent identity and tenant scope come from the
credential rather than from tool-call arguments. Get one self-serve, free, at
[app.gatecoreai.com/developer/portal](https://app.gatecoreai.com/developer/portal). For
anything else, contact [hello@gatecoreai.com](mailto:hello@gatecoreai.com).

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
