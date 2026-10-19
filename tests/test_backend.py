import httpx
import pytest
from aiyucha_mcp.backend import AiyuchaAPI
from aiyucha_mcp.intelligence import domain_history, domain_risk


class FakeBackendClient:
    def __init__(self, reply: httpx.Response, calls: list):
        self.reply = reply
        self.calls = calls

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    async def post(self, url, *, json, headers):
        self.calls.append((url, json, headers))
        return self.reply


@pytest.mark.asyncio
async def test_existing_api_key_and_redacted_projection(monkeypatch):
    calls = []
    reply = httpx.Response(200, json={
        "result": {
            "status": "success", "summary": "Registration date found",
            "facts": [
                {"key": "registration_date", "value": "2012-01-01"},
                {"key": "records.0.main_unit_address", "value": "Private address"},
                {"key": "entities", "value": "user@example.com"},
            ],
            "tables": [{"secret": "not public"}], "raw_provider": {"password": "topsecret"},
        },
        "billing": {"charged": "1.00"},
    })
    monkeypatch.setattr("aiyucha_mcp.backend.httpx.AsyncClient",
                        lambda **kwargs: FakeBackendClient(reply, calls))
    backend = AiyuchaAPI("https://aiyucha.com", "odi_live_dummy_012345678901234567890")
    output = await backend.query("rdap", "example.com")
    assert output["status"] == "ok"
    assert output["result"]["facts"] == [
        {"key": "registration_date", "value": "2012-01-01"}
    ]
    assert "Private address" not in str(output)
    assert "topsecret" not in str(output)
    assert calls[0][0] == "https://aiyucha.com/v1/tools/domain/rdap"
    assert calls[0][2]["Authorization"].startswith("Bearer odi_live_")
    assert calls[0][2]["Idempotency-Key"].startswith("mcp-")
    assert len(calls[0][2]["Idempotency-Key"]) <= 160
    assert calls[0][1] == {"domain": "example.com", "locale": "en"}


@pytest.mark.asyncio
async def test_existing_api_unavailable_returns_unknown(monkeypatch):
    monkeypatch.setenv("AIYUCHA_MCP_EXTENDED_SOURCES", "1")
    calls = []
    reply = httpx.Response(503, json={"error": "provider timeout"})
    monkeypatch.setattr("aiyucha_mcp.backend.httpx.AsyncClient",
                        lambda **kwargs: FakeBackendClient(reply, calls))
    backend = AiyuchaAPI("https://aiyucha.com", "odi_live_dummy_012345678901234567890")
    risk = await domain_risk("example.com", backend=backend)
    assert len(calls) == 3
    assert risk["rating"] == "not_determined"
    assert risk["registry"]["status"] == "unavailable"


@pytest.mark.asyncio
async def test_funded_history_reuses_existing_tool_billing(monkeypatch):
    monkeypatch.setenv("AIYUCHA_MCP_EXTENDED_SOURCES", "1")
    calls = []
    reply = httpx.Response(200, json={"result": {"status": "success", "facts": []}})
    monkeypatch.setattr("aiyucha_mcp.backend.httpx.AsyncClient",
                        lambda **kwargs: FakeBackendClient(reply, calls))
    backend = AiyuchaAPI("https://aiyucha.com", "odi_live_dummy_012345678901234567890")
    result = await domain_history("example.com", backend=backend)
    assert len(calls) == 4
    assert len({headers["Idempotency-Key"] for _, _, headers in calls}) == 4
    assert result["icp_history"]["status"] == "ok"
    assert "domain" in result


@pytest.mark.parametrize("bad", ["http://aiyucha.com", "https://user:pw@aiyucha.com",
                                 "https://aiyucha.com/foo", "file:///etc/passwd"])
def test_disallow_configured_insecure_origin(bad):
    with pytest.raises(ValueError):
        AiyuchaAPI(bad, "odi_live_dummy_012345678901234567890")


@pytest.mark.asyncio
async def test_stable_history_omits_archive_queries_by_default(monkeypatch):
    monkeypatch.delenv("AIYUCHA_MCP_EXTENDED_SOURCES", raising=False)
    calls = []
    reply = httpx.Response(200, json={"result": {"status": "success", "facts": []}})
    monkeypatch.setattr("aiyucha_mcp.backend.httpx.AsyncClient",
                        lambda **kwargs: FakeBackendClient(reply, calls))
    result = await domain_history(
        "example.com",
        backend=AiyuchaAPI("https://aiyucha.com", "odi_live_dummy_012345678901234567890"),
    )
    assert len(calls) == 2
    assert result["archive"]["status"] == "not_checked"
    assert result["historical_site_use"]["status"] == "not_checked"
    assert result["registry"]["status"] == "ok"


@pytest.mark.asyncio
async def test_stable_risk_omits_unavailable_network_sources_by_default(monkeypatch):
    monkeypatch.delenv("AIYUCHA_MCP_EXTENDED_SOURCES", raising=False)
    calls = []
    reply = httpx.Response(200, json={"result": {"status": "success", "facts": []}})
    monkeypatch.setattr("aiyucha_mcp.backend.httpx.AsyncClient",
                        lambda **kwargs: FakeBackendClient(reply, calls))
    result = await domain_risk(
        "example.com",
        backend=AiyuchaAPI("https://aiyucha.com", "odi_live_dummy_012345678901234567890"),
    )
    assert len(calls) == 1
    assert result["registry"]["status"] == "ok"
    assert result["backlink_risk"]["status"] == "not_checked"
    assert result["china_access"]["status"] == "not_checked"
