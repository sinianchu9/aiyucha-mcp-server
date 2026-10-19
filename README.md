# AIYuCha MCP Server — Domain Intelligence for ChatGPT & AI Agents

**Domain valuation · RDAP / WHOIS registration signals · ICP filing research · Domain history · Domain risk assessment · Domain comparison**

[AIYuCha](https://aiyucha.com/en) is a domain intelligence research service. This standalone **Model Context Protocol (MCP) server** makes five domain-analysis tools accessible to ChatGPT and MCP-compatible AI clients over HTTPS Streamable HTTP.

**Live MCP endpoint:** [https://aiyucha.com/mcp](https://aiyucha.com/mcp)  
**Official website:** [AIYuCha.com](https://aiyucha.com/en) · [中文站](https://aiyucha.com/zh)  
**OpenAI demonstration:** [Video walkthrough](https://youtu.be/AFbnz70vTbA)  
**Protocol:** MCP / Streamable HTTP · **Implementation:** Python

> The public MCP endpoint does not require users to register, supply an API key, connect a wallet, or make a payment. The server has its own separately managed research budget. It **does not buy, transfer, or modify domains**.

## Domain intelligence tools

| MCP tool | What it does |
| --- | --- |
| `analyze_domain_features` | Analyzes domain spelling, label length, TLD, name structure, pronounceability hints, and likely business categories. |
| `analyze_domain_value` | Produces an explainable **rule-based structural valuation reference** in USD plus a 0–100 name-structure score. Not a verified market appraisal. |
| `get_domain_history` | Checks available registration **RDAP** records and **China ICP** filing evidence. Additional historical website/archive sources are opt-in for operators. |
| `check_domain_risk` | Reports observed registry-status signals from RDAP. Additional backlink and network sources are opt-in; missing evidence is not labeled as safety. |
| `compare_domains` | Compares two domain names side by side for structural branding characteristics and heuristic value. |

Typical use cases: compare brand domains, research an aged domain before acquisition, assess a name's structural value, inspect public registry status, investigate available China ICP filing signals, and support domain due diligence.

**Scope:** The service examines *public, registrable root domain names*. It rejects URLs, IP addresses, localhost/private addresses, hostnames, and paths. Results identify source availability and distinguish observed records from estimates. They do not establish trademark clearance, registration availability, historic abuse, or actual sale price.

## Connect your AI client

Use the hosted endpoint to connect any client that supports remote MCP over Streamable HTTP. Configuration formats vary by client; a common example is:

```json
{
  "mcpServers": {
    "aiyucha-domain-intelligence": {
      "type": "streamable-http",
      "url": "https://aiyucha.com/mcp"
    }
  }
}
```

For ChatGPT/OpenAI, use the official MCP/plugin connection flow offered in your account and select the same URL. The public GitHub repository is **not** evidence of OpenAI directory approval or publication.

### Example prompts

- “Analyze the branding potential of cloudnova.com using AIYuCha.”
- “Estimate the structural value of example.com and explain the factors.”
- “Find available RDAP registration and ICP evidence for example.com.”
- “Check observed registry risk signals for iana.org.”
- “Compare aiagent.com versus ai-agent.com for a new brand.”

## Run locally

Requires Python **3.11+**. Clone this repository, then run:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[test]"
aiyucha-mcp
```

Local Streamable HTTP endpoint: `http://127.0.0.1:8765/mcp`. By default, the standalone server can use public official-registry RDAP and sampled Internet Archive evidence. Production-style AIYuCha SaaS evidence calls require an independently authorized backend service key; **never commit keys**.

Optional operator-only configuration:

```bash
export AIYUCHA_MCP_BACKEND_URL=https://aiyucha.com
export AIYUCHA_MCP_API_KEY_FILE=/secure/path/to/service-key
# Optional expanded sources; disabled by default in hosted production:
# export AIYUCHA_MCP_EXTENDED_SOURCES=1
aiyucha-mcp
```

Use a trusted HTTPS reverse proxy when hosting publicly. The process binds to loopback by default. Restrict unauthenticated traffic at the edge and protect the backend key outside this repository.

### Docker

```bash
docker build -t aiyucha-mcp-server .
docker run --rm -p 127.0.0.1:8765:8765 aiyucha-mcp-server
```

### Tests

```bash
python -m pytest -q tests/test_intelligence.py tests/test_backend.py tests/test_protocol.py
```

The source follows a small, independently deployable layout:

- `src/aiyucha_mcp/server.py` — five tools, MCP transport, annotations and request logging
- `src/aiyucha_mcp/intelligence.py` — domain validation, name analysis, official RDAP and history evidence
- `src/aiyucha_mcp/backend.py` — optional existing AIYuCha SaaS query bridge, scoped facts and idempotency
- `tests/` — protocol and tool regression tests
- `submission/` — OpenAI-compatible metadata, icon, and review examples
- `docs/` — bilingual usage, integration scope and publication notes

## How the domain data is interpreted

The default hosted evidence profile favors **RDAP + ICP** for domain history and **RDAP** for risk signals. Internet Archive, extended website-history, backlinks, and network observations are available only when an operator deliberately enables supported upstream integrations. Local fallback behavior differs when no AIYuCha backend credential is configured.

A heuristic domain valuation is *not* a recorded sale, professional appraisal, auction quote, or investment promise. A missing or unreachable data source is reported as unavailable, not silently converted into “no risk.” Registrant personal details are not exposed in the public response.

## 中文说明：爱域查域名智能分析 MCP

**爱域查 MCP Server** 将域名价值评估、RDAP / WHOIS 注册局信息、ICP 备案线索、域名历史查询、域名风险信号与域名对比接入 ChatGPT 和其他支持 Model Context Protocol 的 AI 客户端。

- **域名价值评估：** 根据域名长度、后缀、字符结构和命名特征，给出可解释的结构估值参考。
- **老域名及域名历史研究：** 默认可调用注册局 RDAP 和 ICP 相关线索，其他历史数据源按实际配置启用。
- **域名风险查询：** 基于真实可取得的注册状态信号判断，缺失数据明确标注。
- **域名对比：** 将两个域名的品牌命名优势与结构分数并列展示。
- **ChatGPT 接入：** 通过 `https://aiyucha.com/mcp` 直接连接，无需终端用户注册爱域查账户。

更多域名查询服务请访问 [爱域查](https://aiyucha.com/zh)。此仓库只公开独立的对外 MCP 服务与提交资料，不包含爱域查 SaaS、Core、多节点执行器、用户钱包或生产密钥。

## Privacy, support & submission

- [Privacy Policy](https://aiyucha.com/en/privacy)
- [Terms of Service](https://aiyucha.com/en/terms)
- [Support](https://aiyucha.com/en/feedback)
- [OpenAI review material](submission/) · [Review example cases](submission/review-cases.json)

**AIYuCha Domain Intelligence** is a research integration, not a domain registrar, checkout, certificate of ownership, or guarantee of future revenue. Public-source results depend on provider availability. The repository is maintained separately from the site's operational infrastructure.

---

**Relevant topics:** model-context-protocol, mcp-server, chatgpt-mcp, openai-mcp, domain-intelligence, domain-valuation, domain-history, rdap, whois, icp-filing, domain-risk, domain-comparison, python.
