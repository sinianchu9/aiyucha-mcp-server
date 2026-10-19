# Security policy / 安全说明

This repository contains only the public-facing AIYuCha MCP implementation, client configuration and OpenAI review materials. It does not contain production credentials, SaaS wallet provisioning code, Core workers, infrastructure backups or customer databases.

## Report a concern

Please privately contact the operator via the [AIYuCha support form](https://aiyucha.com/en/feedback). Do not post access tokens, vulnerability details involving production keys, or personal information in a public GitHub issue.

## Scope of public tools

- Accepts valid registrable public domain names; rejects URLs, IP addresses and localhost/private hosts.
- Registry requests use explicit, allowlisted endpoints with redirects disabled.
- Public results exclude registrant identity records and raw backend/provider diagnostics.
- The optional SaaS bridge needs a separately provisioned service account; the key must stay outside source control.
- `get_domain_history` and `check_domain_risk` can use internal metered backend queries, so their MCP idempotency hints differ from the three local-only tools.
- None of the five MCP tools offers domain purchases, payments, DNS edits or user-account mutations.

## 报告问题

发现安全问题请通过 [爱域查反馈页面](https://aiyucha.com/zh/feedback) 私下联系。请勿向公开仓库提交真实密钥、私人数据或生产系统敏感信息。
