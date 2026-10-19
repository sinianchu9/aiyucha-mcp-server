"""Protocol-level test: official MCP initialize -> list tools over Streamable HTTP."""
from starlette.testclient import TestClient

from aiyucha_mcp.server import mcp, transport_security_settings


def test_mcp_initialize_and_discover_tools():
    app = mcp.streamable_http_app(stateless_http=True, json_response=True,
                                  transport_security=transport_security_settings())
    with TestClient(app, base_url="https://aiyucha.com") as client:
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "MCP-Protocol-Version": "2025-06-18",
        }
        initialized = client.post("/mcp", headers=headers, json={
            "jsonrpc": "2.0", "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2025-06-18",
                       "capabilities": {},
                       "clientInfo": {"name": "review-smoke", "version": "1.0"}},
        })
        assert initialized.status_code == 200, initialized.text
        result = initialized.json()
        assert "result" in result
        listed = client.post("/mcp", headers=headers, json={
            "jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}
        })
        assert listed.status_code == 200, listed.text
        tools = listed.json()["result"]["tools"]
        assert {tool["name"] for tool in tools} == {
            "analyze_domain_features", "analyze_domain_value", "get_domain_history",
            "check_domain_risk", "compare_domains",
        }
        local_read_tools = {"analyze_domain_features", "analyze_domain_value", "compare_domains"}
        for tool in tools:
            hints = tool["annotations"]
            if tool["name"] in local_read_tools:
                assert hints["readOnlyHint"] is True
                assert hints["idempotentHint"] is True
            else:
                assert hints["readOnlyHint"] is False
                assert hints["idempotentHint"] is False
            assert hints["destructiveHint"] is False
        called = client.post("/mcp", headers=headers, json={
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "analyze_domain_features",
                       "arguments": {"domain": "cloudnova.com"}},
        })
        assert called.status_code == 200, called.text
        payload = called.json()["result"]
        assert payload.get("isError") is not True
        assert "cloudnova.com" in str(payload)
        assert "structural_brand_score" in str(payload)

        # OpenAI's verified Plugin Platform sends Origin: https://platform.openai.com.
        platform_headers = {**headers, "Origin": "https://platform.openai.com"}
        scanned = client.post("/mcp", headers=platform_headers, json={
            "jsonrpc": "2.0", "id": 4,
            "method": "tools/list", "params": {},
        })
        assert scanned.status_code == 200, scanned.text
        assert len(scanned.json()["result"]["tools"]) == 5
