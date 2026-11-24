<div align="center">

<sub><strong>L0NE-6 · BAIPIAO SIGNAL</strong></sub>

# Baipiao Daily

**Baipiao 每日签到 · 多账号隔离 · 签到前后状态回读 · JSONL**

> 当前版本：**v1.0.0**（2026-11-24） · 签到前后各读一次 overview，响应字段和状态回读共同判定

[简体中文](README.md) · [English](docs/README.en.md) · [繁體中文](docs/README.zh-Hant.md) · [日本語](docs/README.ja.md) · [한국어](docs/README.ko.md) · [Português (BR)](docs/README.pt-BR.md)

<img src="https://img.shields.io/badge/Features-Check-in%20Readback-6F42C1?style=for-the-badge" alt="Features" />
<a href="https://github.com/L0NE-6/Baipiao-Daily/releases"><img src="https://img.shields.io/github/v/release/L0NE-6/Baipiao-Daily?style=for-the-badge&label=Release&color=2ea44f&logo=github" alt="Release" /></a>
<a href="https://github.com/L0NE-6/Baipiao-Daily/stargazers"><img src="https://img.shields.io/github/stars/L0NE-6/Baipiao-Daily?style=for-the-badge&label=Stars&color=FFC75F&logo=github" alt="Stars" /></a>
<img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
<img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20Qinglong-4EAA25?style=for-the-badge&logo=linux&logoColor=white" alt="Platform" />
<img src="https://img.shields.io/badge/License-MIT-F472B6?style=for-the-badge" alt="License" />

🔐 bitapi_session 隔离 · 🎁 每日签到 · 👥 多账号 · 🧾 JSONL · 🐧 青龙 · ☁️ GitHub Actions

[⚡ 30 秒速览](#quick-look) · [🔁 协议与回读](#protocol) · [🔐 凭据](#credentials) · [🐧 青龙](#qinglong) · [☁️ Actions](#actions) · [⌨️ CLI](#cli-json) · [✅ 成功判据](#success) · [✦ 星轨](#star-trail)

</div>

---

<a id="usage-policy"></a>
## 🚫 使用边界与禁止倒卖

> [!IMPORTANT]
> **官方版本永久免费。** 未经作者书面许可，禁止倒卖、付费包装、搬运引流、冒充作者，或使用作者身份与二维码制造官方授权假象。

本仓库、脚本、部署说明和 Release 下载保持免费公开。禁止将本项目或其轻度改名版本包装为付费资源、内部版、独家版、会员权益、收费课程、代部署服务或包更新服务；禁止搬运到其他账号、群组、频道、网盘、电商平台或付费社群进行涨粉、截流、倒卖和引流；禁止删除作者与版权信息后冒充原创。

完整规则见 [NOTICE.md](NOTICE.md)。第三方以“下载费 / 激活费 / 内部版 / 代部署 / 会员门槛”等名义收费，均与作者无关，请停止付款并保留证据。

---

<a id="quick-look"></a>
## ⚡ 30 秒速览

| 维度 | 说明 |
| :--- | :--- |
| **做什么** | 使用 `bitapi_session` 调用 Baipiao 每日签到。 |
| **输入** | `BAIPIAO_ACCOUNTS`，或单账号 `BAIPIAO_SESSION`。 |
| **协议** | `GET /api/overview` → `POST /api/checkin` → `GET /api/overview`。 |
| **回读** | 签到后 `checkin.checked_in` 必须为 true，奖励必须为正数。 |
| **输出** | 每账号一条 JSON，最后一条汇总 JSON。 |
| **成功判据** | `claimed=true`、`reward>0`、签到后 `checked_in=true`。 |

---

## 🧭 这是什么 / 覆盖范围

Baipiao 脚本用 `bitapi_session` 作为 Bearer 凭据，先读取 `/api/overview` 判断今日状态，再按需提交 `/api/checkin`，最后再次读取 `/api/overview`。签到接口没有请求体。

### 覆盖范围

- 多账号 `备注|bitapi_session`，也接受包含 `bitapi_session` 的完整 Cookie。
- `--query` / `--status` 只读模式，不发送签到请求。
- 签到前后状态、日期、余额、奖励和余额差值记录。
- 明确区分今日已签、未开放、领取未生效、奖励未确认和状态冲突。
- JSONL 报告、Actions artifact 和可选站点基址。

---

<a id="protocol"></a>
## 🔁 协议与回读流程

### 请求链

```http
GET /api/overview
POST /api/checkin
Authorization: Bearer <bitapi_session>
GET /api/overview
```

`POST /api/checkin` 不发送请求体。脚本把 `bitapi_session` 规范化为 Cookie 请求头；如果输入是完整 Cookie，则保留其中的 `bitapi_session`。

### 关键字段

| 字段 | 类型 | 判定 |
| :--- | :--- | :--- |
| `checkin.checked_in` | boolean | 服务端记录的今日签到状态。 |
| `claimed` | boolean | 本次请求是否发放奖励。 |
| `checked_in` | boolean | 签到响应中的今日状态。 |
| `reward` | number | 本次奖励金额。 |
| `date` | string | 签到日期。 |
| `balance` | number | 账户余额。 |

`claimed=false` 且 `checked_in=true` 表示今日已签到；`claimed=false` 且 `checked_in=false` 表示当前没有可用签到。字段缺失、类型错误、日期冲突或签到后状态未翻转都按失败处理。

---

<a id="credentials"></a>
## 🔐 凭据与环境变量

### 多账号

```text
备注|bitapi_session
备注|bitapi_session=<session>; bitapi_csrf=<csrf>
```

第二列可以是 JWT 本身，也可以是包含 `bitapi_session` 的整段 Cookie 请求头。

### 环境变量

| 变量 | 必填 | 说明 |
| :--- | :---: | :--- |
| `BAIPIAO_ACCOUNTS` | 二选一 | 多账号列表，每行 `备注\|bitapi_session`。 |
| `BAIPIAO_SESSION` | 二选一 | 单账号 `bitapi_session`。 |
| `BAIPIAO_BASE_URL` | 否 | 默认 `https://ai.baipiao.co`。 |

---

## 💻 本地快速开始

### PowerShell

```powershell
python -m pip install -r requirements.txt
$env:BAIPIAO_SESSION = "<bitapi_session>"
python baipiao_daily.py
```

### Bash

```bash
python -m pip install -r requirements.txt
export BAIPIAO_SESSION='<bitapi_session>'
python baipiao_daily.py
```

只读查询使用 `python baipiao_daily.py --query`；只运行第二个账号使用 `--only 2`。

---

<a id="qinglong"></a>
## 🐧 青龙

1. 在青龙依赖管理中安装 `requests`，或执行 `pip3 install -r requirements.txt`。
2. 上传 `baipiao_daily.py` 到脚本目录。
3. 在环境变量中配置 `BAIPIAO_ACCOUNTS` 或 `BAIPIAO_SESSION`。
4. 新建定时任务，命令使用 `task baipiao_daily.py`，不要直接写裸 `python`。
5. 建议北京时间：`7 8 * * *`。青龙按面板本地时间执行。

```bash
pip3 install -r requirements.txt
task baipiao_daily.py
```

---

<a id="actions"></a>
## ☁️ GitHub Actions、Secrets 与定时

工作流：`.github/workflows/baipiao.yml`。

| 事件 | 行为 |
| :--- | :--- |
| `push` 到 `main` | 单元测试、编译检查、Ruff。 |
| `schedule` | 先测试，再执行签到并上传 JSON 报告。 |
| `workflow_dispatch` | 手动执行同一套流程。 |

### Secrets 与变量

| 名称 | 类型 | 说明 |
| :--- | :--- | :--- |
| `BAIPIAO_ACCOUNTS` | Secret | 多账号列表。 |
| `BAIPIAO_SESSION` | Secret | 单账号会话。 |
| `BAIPIAO_BASE_URL` | Repository variable | 可选站点根地址。 |

内置定时为 UTC `7 0 * * *`，对应北京时间约 08:07。未配置凭据时输出 notice 并成功跳过在线执行。

---

<a id="cli-json"></a>
## ⌨️ CLI 与 JSON 输出

```powershell
python baipiao_daily.py
python baipiao_daily.py --query
python baipiao_daily.py --only 2
```

单账号 JSON 示例：

```json
{
  "account": "account_1",
  "provider": "baipiao",
  "result": "CLAIMED",
  "ok": true,
  "claimed": true,
  "checked_in": true,
  "reward": 0.05,
  "date": "2026-11-24",
  "before_checked_in": false,
  "after_checked_in": true,
  "balance_before": 12.5,
  "balance_after": 12.55,
  "balance_delta": 0.05
}
```

| 字段 | 说明 |
| :--- | :--- |
| `before_checked_in` / `after_checked_in` | 签到前后服务端状态。 |
| `reward` / `date` | 本次奖励与签到日期。 |
| `balance_before` / `balance_after` | 前后余额。 |
| `balance_delta` | 余额差，仅作记录。 |
| `response_balance` | 签到响应中的余额，仅在存在时输出。 |

---

<a id="result-codes"></a>
## 🧾 结果码

| 结果码 | 成功 | 含义 |
| :--- | :---: | :--- |
| `CLAIMED` | 是 | 本次领取完成，奖励为正数且状态已翻转。 |
| `ALREADY_CLAIMED` | 是 | 运行前或响应中确认今日已签到。 |
| `AVAILABLE` | 是 | 查询模式确认当前可签到。 |
| `INACTIVE` | 否 | 站点没有报告可用的每日签到。 |
| `CLAIM_NOT_APPLIED` | 否 | 签到请求返回成功，但回读仍为 false。 |
| `CREDIT_UNCONFIRMED` | 否 | 奖励缺失或不是正数。 |
| `STATE_CONFLICT` | 否 | 响应状态或日期与回读结果冲突。 |
| `STATUS_UNRECOGNIZED` | 否 | `/api/overview` 状态结构无法确认。 |
| `AUTH_EXPIRED` | 否 | `bitapi_session` 失效或被拒绝。 |
| `BLOCKED` | 否 | 返回 HTML 验证页而不是 JSON。 |
| `RATE_LIMITED` | 否 | HTTP 429。 |
| `BUSINESS_ERROR` | 否 | 服务端业务错误。 |
| `HTTP_ERROR` | 否 | 非 2xx HTTP 错误。 |
| `NETWORK_ERROR` | 否 | 网络异常或超时。 |
| `INVALID_JSON` | 否 | 返回内容不是 JSON。 |
| `INVALID_RESPONSE` | 否 | JSON 结构或字段类型错误。 |
| `CONFIG_ERROR` | 否 | 环境变量或基址配置错误。 |

---

<a id="success"></a>
## ✅ 成功判据

| 场景 | 必须满足 |
| :--- | :--- |
| 今日新领取 | `claimed=true`、`reward>0`、签到后 `checkin.checked_in=true`。 |
| 今日已领取 | 运行前 `checked_in=true`，或响应明确 `checked_in=true` 且回读仍为 true。 |
| 查询模式 | 只读 `/api/overview`，不得调用签到接口。 |
| 状态冲突 | 前后日期、布尔状态或响应字段不一致时失败。 |

HTTP 200、`claimed=true` 或单个余额字段都不能单独证明奖励到账。

---

## 🧪 测试与静态检查

```bash
python -m unittest discover -s tests -v
python -m compileall -q .
python -m ruff check baipiao_daily.py tests
```

离线测试使用 fake response 和 fake session，覆盖 Cookie 规范化、无请求体 POST、查询模式、已签到短路、重复响应仍需回读、未开放、领取未生效、日期冲突、鉴权失效和脱敏。

---

## 🧱 设计原则

- **前后双读**：签到前后各读一次 `/api/overview`。
- **响应不代替回读**：`claimed` 只是请求回执，最终看服务端状态。
- **无 body 提交**：签到 POST 不携带额外字段。
- **查询只读**：`--query` 不触发签到。
- **账号隔离**：单账号异常只影响本账号。

---

## 🔒 隐私

仓库不包含账号、JWT、Cookie、手机号、邮箱、运行日志或真实响应。`baipiao-report.json` 和 `baipiao-report.jsonl` 已由 `.gitignore` 排除。

---

## 📁 目录结构

```text
Baipiao-Daily/
├── .github/workflows/baipiao.yml
├── assets/
│   ├── donate-alipay.jpg
│   └── donate-wechat.png
├── docs/
│   ├── README.en.md
│   ├── README.zh-Hant.md
│   ├── README.ja.md
│   ├── README.ko.md
│   └── README.pt-BR.md
├── tests/test_baipiao_daily.py
├── CHANGELOG.md
├── LICENSE
├── NOTICE.md
├── THIRD_PARTY_NOTICES.md
├── baipiao_daily.py
├── pyproject.toml
├── README.md
└── requirements.txt
```

---

## 📦 版本与发布

- 当前清单版本：`v1.0.0`，日期 `2026-11-24`。
- 脚本版本与 `baipiao_daily.py` 内的 `VERSION` 保持一致。
- 更新记录见 [CHANGELOG.md](CHANGELOG.md)，下载入口见 [Releases](https://github.com/L0NE-6/Baipiao-Daily/releases)。
- Release 徽标由 GitHub 实时生成；如果页面尚未创建对应 Release，以 `CHANGELOG.md` 和仓库提交为准。

---

## ⚠️ 免责声明

本项目用于个人学习与个人自动化。Baipiao 的活动规则、接口、奖励、风控策略和账号资格由服务方决定。使用前请确认对应服务条款，并自行承担接口变化、账号限制和网络环境带来的风险。

---

## ☕ 支持与投喂

脚本完全免费，赞赏纯自愿，不影响任何功能，也不影响 Issue 响应。

<p align="center">
  <img src="assets/donate-wechat.png" width="260" alt="微信赞赏码" />
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <img src="assets/donate-alipay.jpg" width="260" alt="支付宝收款码" />
</p>
<p align="center"><sub>💚 微信支付（左） &nbsp;|&nbsp; 💙 支付宝（右，支持信用卡 / 花呗）</sub></p>

> 收款码仅用于向作者自愿赞赏。任何第三方以代下载、代部署、内部资源或会员群为由收费，均与作者无关。

---

## 💬 反馈与贡献

- 提交 [Issue](https://github.com/L0NE-6/Baipiao-Daily/issues) 时附运行日志、脱敏后的错误字段和复现步骤。
- 发起 [Pull Request](https://github.com/L0NE-6/Baipiao-Daily/pulls) 时保持单文件运行、离线测试和凭据脱敏约束。
- 不要在任何 Issue、PR、截图或日志中粘贴真实 Token、Cookie、密码、UID、手机号或邮箱。

---

<a id="star-trail"></a>
## ✦ Star History / 星轨

<a href="https://star-history.com/#L0NE-6/Baipiao-Daily&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=L0NE-6/Baipiao-Daily&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=L0NE-6/Baipiao-Daily&type=Date" />
    <img alt="Baipiao-Daily Star History" src="https://api.star-history.com/svg?repos=L0NE-6/Baipiao-Daily&type=Date" />
  </picture>
</a>

<div align="center">
  <sub>L0NE-6 · DAILY SIGNAL &nbsp;|&nbsp; 点个 <b>Star</b>，让下一轮自动化有迹可循</sub>
</div>
