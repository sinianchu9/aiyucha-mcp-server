import asyncio

import httpx
import pytest
from aiyucha_mcp.intelligence import (
    domain_comparison,
    domain_features,
    domain_history,
    domain_risk,
    domain_value,
    normalize_domain,
    rdap_registration,
    wayback_footprint,
)


@pytest.mark.parametrize("bad", [
    "localhost", "127.0.0.1", "http://example.com", "example.com/path",
    "foo.example.com", "example.com:443", "*.example.com",
    "example.com@localhost", "test", "foo..com", "a.com?q=x",
])
def test_reject_non_registrable_or_url(bad):
    with pytest.raises(ValueError):
        normalize_domain(bad)


def test_normalization_and_features():
    assert normalize_domain("CLOUDNOVA.COM.") == "cloudnova.com"
    assert normalize_domain("例子.中国").startswith("xn--")
    f = domain_features("cloudnova.com")
    assert f["name_length"] == 9
    assert "software" in f["possible_industries"]
    assert f["structural_brand_score"] <= 100
    assert domain_value("cloudnova.com")["reference_type"] == "uncalibrated_structural_heuristic"


def test_compare_no_fabricated_percent():
    comparison = asyncio.run(domain_comparison("aiagent.com", "ai-agent.com"))
    assert comparison["structural_preference"] == "aiagent.com"
    assert "brand_percent" not in comparison
    with pytest.raises(ValueError):
        asyncio.run(domain_comparison("EXAMPLE.com", "example.com"))


@pytest.mark.asyncio
async def test_rdap_exposes_no_person_data():
    def handler(req):
        assert req.url.host == "rdap.verisign.com"
        return httpx.Response(200, json={
            "ldhName": "example.com", "status": ["client hold", "active"],
            "events": [{"eventAction": "registration", "eventDate": "2000-01-02T00:00:00Z"}],
            "entities": [{"vcardArray": ["vcard", [["email", {}, "text", "owner@example.org"]]]}],
        })
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        out = await rdap_registration("example.com", client)
    assert out["current_record_created"] == "2000-01-02"
    assert "entities" not in out
    assert "owner@example.org" not in str(out)


@pytest.mark.asyncio
async def test_archive_sample_not_all_history():
    def handler(req):
        assert req.url.host == "web.archive.org"
        return httpx.Response(200, json=[["timestamp"], ["20120101000000"], ["20190202000000"]])
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        out = await wayback_footprint("example.com", client)
    assert out["earliest_sampled_year"] == "2012"
    assert out["scope"].startswith("sampled")


@pytest.mark.asyncio
async def test_risk_only_observed_signals():
    def handler(req):
        if req.url.host == "rdap.verisign.com":
            return httpx.Response(200, json={"ldhName": "example.com", "status": ["serverHold"], "events": []})
        return httpx.Response(503)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        risk = await domain_risk("example.com", client=client)
    assert risk["rating"] == "attention"
    assert risk["confirmed_signals"][0]["signal"] == "serverhold"
    assert "spam backlinks" in risk["not_checked"]


@pytest.mark.asyncio
async def test_missing_providers_never_claim_safe():
    def handler(req):
        return httpx.Response(503)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        out = await domain_risk("example.com", client=client)
        hist = await domain_history("example.com", client=client)
    assert out["rating"] == "not_determined"
    assert not out["confirmed_signals"]
    assert hist["historical_owner"] is None
    assert hist["registry"]["status"] == "unavailable"


@pytest.mark.asyncio
async def test_unsupported_tld_no_dynamic_rdap_url():
    out = await rdap_registration("example.xyz")
    assert out["status"] == "not_checked"


@pytest.mark.asyncio
async def test_rdap_mismatch_discarded():
    def handler(req):
        return httpx.Response(200, json={"ldhName": "different.com", "entities": []})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        out = await rdap_registration("example.com", client)
    assert out["status"] == "unavailable"
