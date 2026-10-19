"""Public no-auth read-only MCP tools. Run: aiyucha-mcp."""
from __future__ import annotations

import json
import logging
import os
from contextlib import contextmanager
from time import perf_counter

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations

from .intelligence import (
    domain_comparison,
    domain_features,
    domain_history,
    domain_risk,
    domain_value,
)

mcp = MCPServer(
    "AIYuCha Domain Intelligence",
    instructions=(
        "Use these tools when users explicitly request research about named public domain names. "
        "Return verified signals with their provenance. Structural valuation is a heuristic, "
        "not a recorded sale price. Missing historical, SEO or abuse data must never become "
        "a positive or negative risk finding. No account, purchase, or update operations."
    ),
)
READ = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True)
# These two research tools consume internal SaaS credits or schedule provider tasks.
METERED = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=True)
LOG = logging.getLogger("aiyucha_mcp.usage")


@contextmanager
def _usage(tool: str):
    started = perf_counter()
    outcome = "success"
    try:
        yield
    except BaseException:
        outcome = "failure"
        raise
    finally:
        LOG.info(json.dumps({"event": "mcp_tool", "tool": tool, "outcome": outcome,
                             "latency_ms": round((perf_counter() - started) * 1000)}))


@mcp.tool(
    title="Analyze domain features",
    description="Examine a registrable domain's spelling, label length, suffix, structural brand fit and possible industries. Rule-based only; no claim of trademark clearance.",
    annotations=READ,
)
def analyze_domain_features(domain: str) -> dict:
    with _usage("analyze_domain_features"):
        return domain_features(domain)


@mcp.tool(
    title="Analyze domain value",
    description="Give a transparent, broad illustrative USD structural price reference based on name and suffix, plus a 0-100 structural score. Does not fetch comparable transactions or guarantee resale value.",
    annotations=READ,
)
def analyze_domain_value(domain: str) -> dict:
    with _usage("analyze_domain_value"):
        return domain_value(domain)


@mcp.tool(
    title="Get domain history",
    description="Read registration RDAP and available ICP filing evidence. Additional archive sources are disabled by default until stability is verified. Does not expose registrant PII.",
    annotations=METERED,
)
async def get_domain_history(domain: str) -> dict:
    with _usage("get_domain_history"):
        return await domain_history(domain)


@mcp.tool(
    title="Check domain risk signals",
    description="Check observed registry RDAP status and reported risk signals. Unstable backlink and network sources are disabled by default until verified; missing data is not a clean-risk finding.",
    annotations=METERED,
)
async def check_domain_risk(domain: str) -> dict:
    with _usage("check_domain_risk"):
        return await domain_risk(domain)


@mcp.tool(
    title="Compare domain names",
    description="Compare two distinct registrable domains' transparent structural brand features and heuristic value. Does not certify market liquidity, ownership, trademark safety or registerability.",
    annotations=READ,
)
async def compare_domains(domain_a: str, domain_b: str) -> dict:
    with _usage("compare_domains"):
        return await domain_comparison(domain_a, domain_b)


def transport_security_settings() -> TransportSecuritySettings:
    # Fixed public-host allowlist prevents DNS rebinding while permitting ChatGPT requests.
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=["aiyucha.com", "127.0.0.1:8765", "localhost:8765"],
        allowed_origins=["https://chatgpt.com", "https://chat.openai.com", "https://platform.openai.com", "https://aiyucha.com"],
    )


def main() -> None:
    # Defaults bind to localhost; use HTTPS reverse proxy to expose /mcp publicly.
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    mcp.run(transport="streamable-http",
            host=os.getenv("AIYUCHA_MCP_BIND", "127.0.0.1"), port=8765,
            transport_security=transport_security_settings(),
            max_request_body_size=16384, max_sessions=256,
            stateless_http=True, json_response=True)


if __name__ == "__main__":
    main()
