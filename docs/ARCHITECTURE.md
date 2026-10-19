# Architecture / 运行架构

```text
ChatGPT / external MCP client
            |
  HTTPS Streamable HTTP
            |
  https://aiyucha.com/mcp
            |
     AIYuCha MCP server
      |            |
local scoring      optional service-account bridge
(domain features,  |                 |
 valuation,        |             AIYuCha SaaS API
 comparison)       |                 |
                   +---- RDAP / ICP and other configured providers
```

The public MCP server is a **standalone Python service**. It is not the AIYuCha SaaS application, DigDomain mining engine, Core worker infrastructure or payment system.

### Tool execution

- Local deterministic tools: `analyze_domain_features`, `analyze_domain_value`, `compare_domains`. Their calculations use explicit naming heuristics and no upstream paid calls.
- Research tools: `get_domain_history` and `check_domain_risk`. When a trusted backend API key is provided, they reuse AIYuCha's existing, metered SaaS API. By default, the hosted service uses RDAP plus ICP for history and RDAP alone for risk.
- Without an authorized backend key, the implementation can use selected official registry RDAP endpoints and sampled Internet Archive CDX history. Outputs reflect this narrower fallback.
- Expanded sources (`AIYUCHA_MCP_EXTENDED_SOURCES=1`) require separately configured provider reliability and cost controls. They are not enabled in the documented default hosted profile.

### Privacy and safe operation

Inputs are at most two registrable domain names, never user-supplied HTTP targets. Domain URLs and private/local network targets are rejected. Requests to external sources use fixed destinations with no redirect following. The response bridge only returns selected public-data facts and omits registrant personal data. Operator credentials and internal budgets are excluded from this repository.

For production, bind the process to loopback or a private container network; place TLS and request throttling at the reverse proxy; retain logs and usage metrics under your actual published privacy policies. Monitoring and accounting of provider calls belong to the operator's separately managed environment.

### 中文简述

ChatGPT 通过 `https://aiyucha.com/mcp` 调用五项域名分析工具。名称评分、结构估值和域名对比在 MCP 服务中完成；RDAP/ICP 等证据查询可由既有 SaaS 服务账户处理。此公开仓库不包含主站后端、采集集群、Dig 引擎或生产财务/用户资料。
