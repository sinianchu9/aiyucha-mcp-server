"""Use existing AIYuCha paid tool API and its credit ledger, never a parallel wallet."""
from __future__ import annotations

import json
import logging
import os
from time import perf_counter
from urllib.parse import urlsplit
from uuid import uuid4

import httpx

LOG = logging.getLogger("aiyucha_mcp.usage")
API_PATHS = {
    "rdap": "/v1/tools/domain/rdap",
    "archive": "/v1/tools/history/archive-footprint",
    "site_history": "/v1/tools/history/site-history",
    "icp": "/v1/tools/china/icp-history",
    "backlink_risk": "/v1/tools/seo/backlink-risk",
    "china_access": "/v1/tools/china/accessibility",
}
# Allowed fields are the result contract already projected for public API customers.
# This module never forwards raw provider responses or registrant entity data.


class AiyuchaAPI:
    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        url = (base_url or os.getenv("AIYUCHA_MCP_BACKEND_URL", "")).rstrip("/")
        self.secret = api_key or os.getenv("AIYUCHA_MCP_API_KEY", "")
        if not self.secret and os.getenv("AIYUCHA_MCP_API_KEY_FILE"):
            from pathlib import Path
            path = Path(os.environ["AIYUCHA_MCP_API_KEY_FILE"])
            if not path.is_file() or path.is_symlink():
                raise ValueError("The configured MCP API key file must be a regular file.")
            self.secret = path.read_text(encoding="utf-8").strip()
        parsed = urlsplit(url)
        if not url or not self.secret:
            self.base = None
        elif parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
            raise ValueError("AIYUCHA_MCP_BACKEND_URL must be an HTTPS origin without credentials or paths.")
        else:
            self.base = url

    async def query(self, tool: str, domain: str) -> dict:
        if tool not in API_PATHS:
            raise ValueError("Unsupported provider tool.")
        if not self.base:
            return {"status": "not_configured", "source": "AIYuCha SaaS", "reason": "Service account API key is not provisioned."}
        started = perf_counter()
        outcome = "unavailable"
        spent = None
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(18, connect=3), follow_redirects=False, trust_env=False) as client:
                reply = await client.post(
                    self.base + API_PATHS[tool],
                    json={"domain": domain, "locale": "en"},
                    headers={"Authorization": "Bearer " + self.secret, "Accept": "application/json",
                             "Idempotency-Key": f"mcp-{uuid4().hex}"},
                )
            if reply.status_code != 200:
                outcome = f"http_{reply.status_code}"
                return {"status": "unavailable", "source": "AIYuCha SaaS",
                        "reason": "Backend query was not available", "http_status": reply.status_code}
            data = reply.json()
            projected = data.get("result")
            if not isinstance(projected, dict):
                return {"status": "unavailable", "source": "AIYuCha SaaS", "reason": "Invalid result contract"}
            # Public API's projected result is already explicitly field-allowlisted.
            # Omit any raw_provider/diagnostics fields and limit response size.
            allowed_fact_keys = {
                "statuses", "registration_date", "expiration_date", "transfer_date",
                "last_changed", "nameservers", "registrar_name",
                "first_seen_year", "last_seen_year", "active_years", "history_span_years",
                "years", "sampled_snapshot_count", "analyzed_snapshot_count",
                "first_analyzed_year", "last_analyzed_year", "classification_counts",
                "normal_ratio", "continuity.mean_topic_similarity",
                "continuity.low_similarity_pairs", "record_count", "total",
                "records.0.unit_name", "records.0.main_licence",
                "records.0.service_licence", "records.0.nature_name",
                "backlinks_spam_score", "derived.risk_flags",
                "derived.referring_ip_diversity", "derived.referring_subnet_diversity",
                "platforms.cn_network", "details.hard_stop",
                "details.upstream.cn_observation_count",
                "details.upstream.global_observation_count",
            }
            fact_rows = projected.get("facts")
            facts = [{"key": row["key"], "value": row.get("value")}
                     for row in fact_rows if isinstance(row, dict)
                     and row.get("key") in allowed_fact_keys] if isinstance(fact_rows, list) else []
            safe = {"status": projected.get("status"), "facts": facts[:30]}
            for key in ("summary", "display_confidence", "observed_at"):
                value = projected.get(key)
                if isinstance(value, (int, float, str)) and len(str(value)) < 900:
                    safe[key] = value
            if len(json.dumps(safe, ensure_ascii=False, default=str)) > 12000:
                safe["facts"] = safe["facts"][:10]
            billing = data.get("billing")
            if isinstance(billing, dict):
                spent = str(billing.get("charged_credits") or billing.get("charged") or "0")
            outcome = "success" if str(projected.get("status")).lower() in {"success", "partial", "empty", "returned"} else "unavailable"
            return {"status": "ok" if outcome == "success" else "unavailable",
                    "source": "AIYuCha SaaS existing tool API",
                    "tool": tool, "result": safe}
        except (httpx.HTTPError, ValueError, TypeError):
            return {"status": "unavailable", "source": "AIYuCha SaaS", "reason": "Backend query failed"}
        finally:
            LOG.info(json.dumps({"event": "mcp_backend_tool", "tool": tool,
                                 "outcome": outcome, "charged_credits_reported": spent,
                                 "latency_ms": round((perf_counter() - started) * 1000)}))
