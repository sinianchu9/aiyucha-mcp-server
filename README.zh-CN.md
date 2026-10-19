# 爱域查 MCP Server — ChatGPT 域名价值评估、备案与历史查询

[English README](README.md) · [爱域查网站](https://aiyucha.com/zh) · [MCP 接口](https://aiyucha.com/mcp)

**爱域查 Domain Intelligence MCP** 是独立的 Python MCP 服务，通过 Streamable HTTP 把域名研究工具开放给 ChatGPT、OpenAI 和其他支持 Model Context Protocol 的 AI 客户端。

## 已开放的五项工具

| 工具名 | 用途 |
| --- | --- |
| `analyze_domain_features` | 域名字符结构、后缀、可读性、潜在行业与品牌命名分析 |
| `analyze_domain_value` | 域名结构价值参考、0–100 结构评分及估值因素说明 |
| `get_domain_history` | 注册局 RDAP、ICP备案线索；其他历史档案源按配置选择启用 |
| `check_domain_risk` | 注册状态等有证据的风险信号；未查询的数据会明确标注 |
| `compare_domains` | 两个域名的结构分数、品牌特征和估值参考对比 |

它适合**域名投资研究、品牌域名选择、老域名尽调、域名历史查询和 ICP 备案线索研究**。估值为规则化结构参考，不是实际交易成交价；注册局日期也不等同于域名最早出现时间。

## 直接连接

公开地址：**https://aiyucha.com/mcp**，普通终端用户无需额外注册爱域查账户。

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

具体粘贴位置请以 MCP 客户端版本为准。OpenAI 平台中的审核、发布状态由平台管理；公开 GitHub 仓库不代表审核通过。

## 本地运行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
aiyucha-mcp
```

访问 `http://127.0.0.1:8765/mcp`。本地未配置后端服务密钥时可使用受限的官方 RDAP 与 Internet Archive 抽样查询；如需调用已有爱域查 SaaS 后端，须由运营方独立授权和配置 API 密钥，切勿上传至 GitHub。

```bash
python -m pytest -q tests/test_intelligence.py tests/test_backend.py tests/test_protocol.py
```

更多资料参见 [架构说明](docs/ARCHITECTURE.md)、[OpenAI 提交说明](docs/OPENAI_SUBMISSION.md)、[安全政策](SECURITY.md)。

官网：[aiyucha.com](https://aiyucha.com/zh) · [隐私政策](https://aiyucha.com/en/privacy) · [技术反馈](https://aiyucha.com/en/feedback)

**搜索关键词：** 爱域查、域名估值 MCP、域名价值评估、RDAP 查询、WHOIS、ICP备案查询、域名历史查询、ChatGPT 域名工具、老域名分析、域名风险检测、MCP Server。
