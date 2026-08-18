#!/usr/bin/env python3
"""Discover GateCore marketplace listings and fetch one listing's contract.

Standard library only. No key or account required.

    python3 discover.py                 # list published listings
    python3 discover.py <listing_id>    # fetch one listing and its contract
"""
import json
import sys
import urllib.request

ENDPOINT = "https://mcp.gatecoreai.com/mcp"
# Both parts of this Accept header are required. Without it the endpoint
# returns 406, which is a transport error and not an auth error.
ACCEPT = "application/json, text/event-stream"


class GateCoreMCP:
    def __init__(self, endpoint=ENDPOINT, api_key=None):
        self.endpoint = endpoint
        self.api_key = api_key
        self.session_id = None

    def _post(self, body, expect_reply=True):
        headers = {"Content-Type": "application/json", "Accept": ACCEPT}
        if self.session_id:
            headers["MCP-Session-Id"] = self.session_id
        if self.api_key:
            headers["Authorization"] = "Bearer " + self.api_key
        request = urllib.request.Request(
            self.endpoint, data=json.dumps(body).encode(), headers=headers, method="POST"
        )
        with urllib.request.urlopen(request) as response:
            # The server issues the session on initialize.
            session_id = response.headers.get("mcp-session-id")
            if session_id and not self.session_id:
                self.session_id = session_id
            raw = response.read().decode()
        if not expect_reply:
            return None
        # Replies arrive as Server-Sent Events, so the JSON is on a "data: " line.
        for line in raw.splitlines():
            if line.startswith("data: "):
                return json.loads(line[6:])
        return json.loads(raw)

    def connect(self):
        """Perform the initialize handshake. Nothing else works until this runs."""
        self._post({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "gatecore-example", "version": "1.0.0"},
            },
        })
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"},
                   expect_reply=False)
        return self

    def call_tool(self, name, arguments=None):
        reply = self._post({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments or {}},
        })
        result = reply["result"]
        text = result["content"][0]["text"]
        if result.get("isError"):
            raise RuntimeError(text)
        return text


def main():
    client = GateCoreMCP().connect()
    try:
        if len(sys.argv) > 1:
            # get_listing returns the full machine-enforceable contract: price
            # in cents, required scopes, minimum trust, target, and data
            # classification.
            print(client.call_tool("get_listing", {"listing_id": sys.argv[1]}))
        else:
            # Every argument is optional. Narrow with query, tags,
            # max_price_cents, or min_trust.
            print(client.call_tool("discover_listings", {}))
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
