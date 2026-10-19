"""Evidence-labeled public domain research. No account, charge or data writes."""
from __future__ import annotations

import asyncio
import os
import re
from ipaddress import ip_address
from typing import Any

import httpx
import idna

from .backend import AiyuchaAPI

# Explicit registry-owned endpoints only. No user-provided destination or redirects.
REGISTRY_RDAP = {
    "com": "https://rdap.verisign.com/com/v1/domain/",
    "net": "https://rdap.verisign.com/net/v1/domain/",
    "cn": "https://rdap.cnnic.cn/domain/",
    "org": "https://rdap.publicinterestregistry.org/rdap/domain/",
}
MULTI_LABEL_SUFFIXES = {"com.cn", "net.cn", "org.cn", "gov.cn", "edu.cn", "co.uk", "org.uk", "com.au", "co.jp"}
TECH = {"ai", "cloud", "data", "dev", "code", "tech", "digital", "app", "bot", "nova", "pixel", "stack", "byte", "compute", "agent"}
TRADE = {"shop", "store", "market", "buy", "sale", "pay", "trade", "deal", "cart"}
BUSINESS = {"biz", "brand", "consult", "group", "global", "office", "pro"}
DOMAINS_MAX = 2
TIMEOUT = httpx.Timeout(5.5, connect=2.5)
ARCHIVE_API = "https://web.archive.org/cdx/search/cdx"


def normalize_domain(raw: str) -> str:
    """Require a public registrable domain, never a URL, IP, localhost or subdomain."""
    if not isinstance(raw, str) or len(raw) > 253 or not raw or raw != raw.strip():
        raise ValueError("Provide one domain name (e.g. example.com).")
    name = raw.strip().rstrip(".").lower()
    if any(c in name for c in "/\\:@?&#%* \r\t\n") or name.startswith("."):
        raise ValueError("Enter a domain name, without a URL, port, wildcard or path.")
    try:
        ip_address(name.strip("[]"))
    except ValueError:
        pass
    else:
        raise ValueError("IP addresses are not supported.")
    try:
        ascii_name = idna.encode(name, uts46=True, std3_rules=True).decode("ascii")
    except idna.IDNAError as exc:
        raise ValueError("Invalid domain name.") from exc
    parts = ascii_name.split(".")
    if len(parts) < 2 or any(not p or len(p) > 63 for p in parts):
        raise ValueError("A registrable domain and suffix are required.")
    suffix = ".".join(parts[-2:]) if ".".join(parts[-2:]) in MULTI_LABEL_SUFFIXES else parts[-1]
    if len(parts) != (len(suffix.split(".")) + 1):
        raise ValueError("Provide a registrable root domain, not a hostname.")
    label = parts[0]
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label):
        raise ValueError("Invalid domain label.")
    if not re.fullmatch(r"[a-z]{2,63}", parts[-1]) and not parts[-1].startswith("xn--"):
        raise ValueError("Invalid public suffix.")
    return ascii_name


def domain_features(domain: str) -> dict[str, Any]:
    domain = normalize_domain(domain)
    suffix = next((s for s in MULTI_LABEL_SUFFIXES if domain.endswith("." + s)), domain.rsplit(".", 1)[1])
    label = domain[: -len(suffix) - 1]
    words = []
    for word in sorted(TECH | TRADE | BUSINESS, key=lambda s: (-len(s), s)):
        if word in label and len(word) >= 3:
            words.append(word)
    industries = []
    if any(w in TECH for w in words) or "ai" == label[:2]:
        industries.extend(["software", "AI and developer tools"])
    if any(w in TRADE for w in words):
        industries.append("commerce")
    if any(w in BUSINESS for w in words):
        industries.append("business services")
    if not industries:
        industries.append("general brand")
    hyphens = label.count("-")
    digits = sum(c.isdigit() for c in label)
    readability = bool(label.isalpha() and not label.startswith("xn--"))
    score = round(max(5, min(95, 55 + (14 if suffix == "com" else 6 if suffix in {"net", "org"} else 0)
        + (15 if len(label) <= 5 else 10 if len(label) <= 8 else 4 if len(label) <= 12 else -8)
        - hyphens * 12 - digits * 6 + (4 if readability else 0))))
    drivers = [f".{suffix} suffix", f"{len(label)}-character second-level label"]
    if readability:
        drivers.append("alphabetic spelling")
    if words:
        drivers.append("recognizable fragments: " + ", ".join(words[:5]))
    limitations = []
    if hyphens:
        limitations.append("hyphen may reduce spoken-word clarity")
    if digits:
        limitations.append("digits may increase spelling ambiguity")
    if len(label) > 15:
        limitations.append("long second-level label")
    return {
        "domain": domain,
        "name": label,
        "suffix": suffix,
        "name_length": len(label),
        "hyphens": hyphens,
        "digits": digits,
        "easy_to_spell_hint": readability and len(label) <= 12,
        "recognized_fragments": words[:6],
        "possible_industries": industries,
        "structural_brand_score": score,
        "positive_factors": drivers,
        "tradeoffs": limitations,
        "method": "transparent rule-based structural assessment; not a trademark or market-sales check",
    }


def domain_value(domain: str) -> dict[str, Any]:
    f = domain_features(domain)
    score = f["structural_brand_score"]
    # Structural reference: deliberately wide and explicitly not labeled an observed sale.
    base = 100 if score < 45 else 300 if score < 60 else 600 if score < 75 else 1400 if score < 88 else 3000
    return {
        "domain": f["domain"],
        "structural_value_score": score,
        "reference_range_usd": {"low": base // 2, "high": base * 8},
        "reference_type": "uncalibrated_structural_heuristic",
        "method": "naming length, characters, suffix and word fragments only; no comparable sales",
        "factors": f["positive_factors"],
        "tradeoffs": f["tradeoffs"],
        "market_sales_verified": False,
        "available_for_registration": None,
        "valuation_basis": "structure_only",
    }


def _registry_endpoint(domain: str) -> str | None:
    suffix = domain.rsplit(".", 1)[-1]
    base = REGISTRY_RDAP.get(suffix)
    return (base + domain) if base else None


def _event_date(events: list[Any], action: str) -> str | None:
    for e in events:
        if isinstance(e, dict) and e.get("eventAction", "").lower() == action:
            value = e.get("eventDate")
            if isinstance(value, str):
                return value[:10]
    return None


async def rdap_registration(domain: str, client: httpx.AsyncClient | None = None) -> dict[str, Any]:
    domain = normalize_domain(domain)
    endpoint = _registry_endpoint(domain)
    if not endpoint:
        return {"status": "not_checked", "source": None, "reason": "No verified registry endpoint configured for this suffix."}
    owns_client = client is None
    if owns_client:
        client = httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=False, trust_env=False)
    try:
        r = await client.get(endpoint, headers={"Accept": "application/rdap+json"})
        if r.status_code == 404:
            return {"status": "not_found", "source": endpoint.split("/domain/")[0], "registration_status": "registry_record_not_found"}
        if r.status_code != 200:
            return {"status": "unavailable", "reason": f"registry HTTP {r.status_code}"}
        data = r.json()
        if not isinstance(data, dict) or not data.get("ldhName"):
            return {"status": "unavailable", "reason": "Incomplete RDAP response"}
        if data["ldhName"].lower().rstrip(".") != domain:
            return {"status": "unavailable", "reason": "RDAP domain mismatch"}
        events = data.get("events") if isinstance(data.get("events"), list) else []
        statuses = [s for s in data.get("status", []) if isinstance(s, str)] if isinstance(data.get("status"), list) else []
        return {"status": "found", "source": endpoint.split("/domain/")[0],
            "current_record_created": _event_date(events, "registration"),
            "expires": _event_date(events, "expiration"),
            "registry_statuses": statuses[:12],
            "registrant": None}  # Never return personal RDAP entities.
    except (httpx.HTTPError, ValueError, TypeError, KeyError):
        return {"status": "unavailable", "reason": "Registry request failed"}
    finally:
        if owns_client:
            await client.aclose()


async def wayback_footprint(domain: str, client: httpx.AsyncClient | None = None) -> dict[str, Any]:
    domain = normalize_domain(domain)
    owns_client = client is None
    if owns_client:
        client = httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=False, trust_env=False)
    try:
        r = await client.get(ARCHIVE_API, params={"url": domain, "output": "json",
            "filter": "statuscode:200", "collapse": "timestamp:4", "fl": "timestamp",
            "limit": "100"})
        if r.status_code != 200:
            return {"status": "unavailable", "source": "Internet Archive CDX", "reason": f"archive HTTP {r.status_code}"}
        rows = r.json()
        years = sorted({row[0][:4] for row in rows[1:]
            if isinstance(row, list) and row and isinstance(row[0], str)
            and re.fullmatch(r"\d{14}", row[0])})
        return {"status": "sampled", "source": "Internet Archive CDX",
            "sampled_years": years, "earliest_sampled_year": years[0] if years else None,
            "latest_sampled_year": years[-1] if years else None,
            "scope": "sampled successful archived captures; not a full-site review"}
    except (httpx.HTTPError, ValueError, TypeError, IndexError):
        return {"status": "unavailable", "source": "Internet Archive CDX", "reason": "Archive request failed"}
    finally:
        if owns_client:
            await client.aclose()


async def domain_history(domain: str, *, client: httpx.AsyncClient | None = None,
                         backend: AiyuchaAPI | None = None) -> dict[str, Any]:
    domain = normalize_domain(domain)
    service = backend or AiyuchaAPI()
    # When funded, reuse exactly the existing product API / API-key attribution / credit ledger.
    if service.base is not None:
        if os.getenv("AIYUCHA_MCP_EXTENDED_SOURCES") == "1":
            rdap, archive, site_history, icp = await asyncio.gather(
                service.query("rdap", domain), service.query("archive", domain),
                service.query("site_history", domain), service.query("icp", domain))
        else:
            rdap, icp = await asyncio.gather(
                service.query("rdap", domain), service.query("icp", domain))
            archive = {"status": "not_checked", "source": "Internet Archive"}
            site_history = {"status": "not_checked", "source": "AIYuCha site history"}
        return {
            "domain": domain, "registry": rdap, "archive": archive,
            "historical_site_use": site_history, "icp_history": icp,
            "historical_owner": None, "registration_cycles_or_transfers": None,
            "notes": "Historical evidence comes from independently projected AIYuCha sources; missing records are not claims of absence.",
        }
    reg, archive = await asyncio.gather(rdap_registration(domain, client), wayback_footprint(domain, client))
    return {
        "domain": domain,
        "registry": reg, "archive": archive,
        "historical_website_type": None,
        "historical_owner": None,
        "historical_icp_filing": None,
        "registration_cycles_or_transfers": None,
        "notes": "RDAP registration date covers the current registration record, not necessarily the first-ever registration. Website type and ICP require separate verified data.",
    }


async def domain_risk(domain: str, *, client: httpx.AsyncClient | None = None,
                      backend: AiyuchaAPI | None = None) -> dict[str, Any]:
    service = backend or AiyuchaAPI()
    if service.base is not None:
        domain = normalize_domain(domain)
        # All requests use the existing product catalog and normal per-module settlement.
        if os.getenv("AIYUCHA_MCP_EXTENDED_SOURCES") == "1":
            reg, backlink, china = await asyncio.gather(
                service.query("rdap", domain),
                service.query("backlink_risk", domain),
                service.query("china_access", domain),
            )
        else:
            reg = await service.query("rdap", domain)
            backlink = {"status": "not_checked", "source": "AIYuCha backlink data"}
            china = {"status": "not_checked", "source": "AIYuCha network observation"}
        # Do not transmute a provider timeout into a clean bill of health.
        return {
            "domain": domain, "rating": "evidence_available" if any(
                x["status"] == "ok" for x in (reg, backlink, china)) else "not_determined",
            "registry": reg, "backlink_risk": backlink, "china_access": china,
            "unverified": ["Google manual action", "legal disputes", "historical fraud",
                           "trademark clearance"],
            "notes": "Interpret confirmed source findings only. Coverage varies per query.",
        }
    history = await domain_history(domain, client=client)
    reg = history["registry"]
    states = [x.lower().replace(" ", "") for x in reg.get("registry_statuses", [])]
    problematic = sorted(set(states) & {"clienthold", "serverhold", "pendingdelete", "redemptionperiod"})
    signals = [{"category": "registry", "signal": x, "evidence": "official registry RDAP status"} for x in problematic]
    return {
        "domain": history["domain"], "rating": "attention" if signals else "not_determined",
        "confirmed_signals": signals,
        "checked": {"registry_status": reg["status"], "archive_footprint": history["archive"]["status"]},
        "not_checked": ["spam backlinks", "search penalties", "trademark disputes",
                        "archived page content", "adult/gambling/fraud history", "ICP filing history"],
        "interpretation": "No detected RDAP registry hold is not evidence that the domain is otherwise safe.",
    }


async def domain_comparison(a: str, b: str) -> dict[str, Any]:
    na, nb = normalize_domain(a), normalize_domain(b)
    if na == nb:
        raise ValueError("Compare two different domains.")
    fa, fb = domain_features(na), domain_features(nb)
    vals = {na: domain_value(na), nb: domain_value(nb)}
    winner = na if fa["structural_brand_score"] > fb["structural_brand_score"] else nb if fb["structural_brand_score"] > fa["structural_brand_score"] else None
    return {
        "domains": [fa, fb], "structural_values": vals,
        "structural_preference": winner or "tie",
        "score_difference": abs(fa["structural_brand_score"] - fb["structural_brand_score"]),
        "basis": "structural naming rules; market transaction, trademark, SEO and availability not verified",
    }
