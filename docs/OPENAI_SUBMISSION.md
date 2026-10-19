# OpenAI / ChatGPT submission — AIYuCha Domain Intelligence

This repository mirrors the **public service and review metadata** for the existing AIYuCha Domain Intelligence integration, version **1.0.4**.

| Field | Value |
| --- | --- |
| Name | AIYuCha Domain Intelligence |
| MCP URL | `https://aiyucha.com/mcp` |
| Transport | Streamable HTTP (HTTPS) |
| End-user authentication | None |
| Category | Education & Research |
| Commerce | None |
| Demo walkthrough | https://youtu.be/AFbnz70vTbA |
| Publisher website | https://aiyucha.com/en |
| Privacy / Terms / Support | https://aiyucha.com/en/privacy · https://aiyucha.com/en/terms · https://aiyucha.com/en/feedback |
| Review examples | Five positive and three negative cases in `submission/review-cases.json` |

**Directory publication status:** A public GitHub repository and reachable MCP endpoint do **not** imply that OpenAI approved or published the integration. The owner's actual status is managed in the OpenAI Developer Portal.

## What reviewers can test

The five tools are `analyze_domain_features`, `analyze_domain_value`, `get_domain_history`, `check_domain_risk` and `compare_domains`. Three tools perform local structural analysis; two may use internal paid data integrations (without charging ChatGPT end users). Invalid addresses are rejected and no domain purchase/payment action exists.

Review materials:
- `submission/plugin.json` and `submission/mcp.json` — canonical review manifests
- `submission/assets/aiyucha-logo.svg` — source icon
- `submission/review-cases.json` — 5 positive and 3 negative test cases
- `.codex-plugin/plugin.json`, `.mcp.json`, `plugin.json`, `mcp.json` — exact connected plugin release v1.0.4 metadata
- `python ops/build_plugin_zip.py` — package review manifests as a ZIP

## Review notes

1. Verify domain ownership and the real HTTPS MCP endpoint in the OpenAI portal.
2. Scan the five live tools and check the manifest's test cases.
3. Supply the authentic video walkthrough and public policy/support URLs.
4. The publisher handles review submission, attestations and any eventual publication.

Do not create a duplicate plugin when updating the existing entry. Never put SaaS service API keys or customer data into the manifest.
