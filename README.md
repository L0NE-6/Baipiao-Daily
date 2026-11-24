<div align="center">

<sub><strong>L0NE-6 · BAIPIAO SIGNAL</strong></sub>

# Baipiao Daily

**Baipiao 每日签到 · 多账号隔离 · 签到前后状态回读 · JSONL**

> 当前版本：**v1.0.0**（2026-11-24） · 单文件运行 · 不把 HTTP 200 冒充签到成功

[简体中文](README.md) · [English](docs/README.en.md) · [繁體中文](docs/README.zh-Hant.md) · [日本語](docs/README.ja.md) · [한국어](docs/README.ko.md) · [Português (BR)](docs/README.pt-BR.md)

<img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20Qinglong-4EAA25?style=for-the-badge" />
<img src="https://img.shields.io/badge/Deploy-GitHub%20Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white" />
<img src="https://img.shields.io/badge/License-MIT-F472B6?style=for-the-badge" />

</div>

## 30 秒速览

| 维度 | 说明 |
| :--- | :--- |
| 做什么 | 使用 `bitapi_session` 调用 Baipiao 每日签到。 |
| 请求 | `POST https://ai.baipiao.co/api/checkin`，Bearer 鉴权，无 body。 |
| 回读 | 签到前读取 `/api/overview`，签到后再次读取 `/api/overview`。 |
| 输出 | 每账号一条 JSON，最后一条汇总 JSON。 |
| 成功 | 领取后 `overview.checkin.checked_in=true`，且响应给出正数 `reward`。 |
| 依赖 | Python 3.9+，运行时仅依赖 `requests`。 |

## 接口流程

```text
GET /api/overview
  |
  +-- checkin.checked_in=true  -> ALREADY_CLAIMED
  |
  +-- checkin.checked_in=false
        |
        +-> POST /api/checkin
              Authorization: Bearer <bitapi_session>
              no request body
        |
        +-> GET /api/overview
              checkin.checked_in must be true
```

固定接口契约：

| 字段 | 类型 | 语义 |
| :--- | :--- | :--- |
| `claimed` | boolean | `true` 表示本次请求发放了奖励。 |
| `checked_in` | boolean | 服务端记录的当日签到状态。 |
| `reward` | number | 本次奖励金额。 |
| `date` | string | 签到日期。 |
| `balance` | number | 签到响应中的账户余额。 |

`claimed=false` 且 `checked_in=true` 表示当日已经签到。
`claimed=false` 且 `checked_in=false` 表示站点没有报告可用的每日签到。
字段缺失、类型错误或签到后状态未翻转都按失败处理。

## 凭据

### 多账号

`BAIPIAO_ACCOUNTS` 每行一个账号：

```text
备注|bitapi_session
```

示例：

```text
账号一|<bitapi_session>
账号二|bitapi_session=<bitapi_session>; bitapi_csrf=<csrf>
```

第二列可以是 JWT 本身，也可以是包含 `bitapi_session` 的整段 Cookie 请求头。

### 单账号

```powershell
$env:BAIPIAO_SESSION = "<bitapi_session>"
```

| 变量 | 必填 | 说明 |
| :--- | :---: | :--- |
| `BAIPIAO_ACCOUNTS` | 二选一 | 多账号列表。 |
| `BAIPIAO_SESSION` | 二选一 | 单账号 `bitapi_session`。 |
| `BAIPIAO_BASE_URL` | 否 | 默认 `https://ai.baipiao.co`。 |

脚本输出只显示备注，不显示 JWT、Cookie 或完整账号。

## 本地运行

```powershell
python -m pip install -r requirements.txt

$env:BAIPIAO_SESSION = "<bitapi_session>"
python baipiao_daily.py
```

多账号：

```powershell
$env:BAIPIAO_ACCOUNTS = @"
账号一|<bitapi_session>
账号二|<bitapi_session>
"@
python baipiao_daily.py
```

只查状态，不调用签到接口：

```powershell
python baipiao_daily.py --query
```

只运行第二个账号：

```powershell
python baipiao_daily.py --only 2
```

## 青龙面板

| 步骤 | 操作 |
| :---: | :--- |
| 1 | 在依赖管理安装 `requests`。 |
| 2 | 上传 `baipiao_daily.py`。 |
| 3 | 环境变量新增 `BAIPIAO_ACCOUNTS` 或 `BAIPIAO_SESSION`。 |
| 4 | 新建定时任务，命令填 `task baipiao_daily.py`。 |
| 5 | 建议北京时间每天 `08:07` 运行一次。 |

## GitHub Actions

仓库内置 [`.github/workflows/baipiao.yml`](.github/workflows/baipiao.yml)。

| 事件 | 行为 |
| :--- | :--- |
| push 到 `main` | 运行单元测试、编译检查和 Ruff。 |
| schedule | 先测试，再执行签到并上传 JSON 报告。 |
| workflow_dispatch | 手动执行同一套流程。 |

### Secrets

| Secret | 必填 | 值 |
| :--- | :---: | :--- |
| `BAIPIAO_ACCOUNTS` | 二选一 | 多账号列表。 |
| `BAIPIAO_SESSION` | 二选一 | 单账号会话。 |

未配置凭据时，定时任务输出明确的跳过通知并成功结束。配置凭据后，脚本失败或回读未确认会让任务保持失败状态。

## 输出字段

单账号结果示例：

```json
{
  "account": "account_1",
  "provider": "baipiao",
  "result": "CLAIMED",
  "ok": true,
  "claimed": true,
  "before_checked_in": false,
  "after_checked_in": true,
  "reward": 0.05,
  "balance_before": 12.5,
  "balance_after": 12.55,
  "balance_delta": 0.05
}
```

| 字段 | 说明 |
| :--- | :--- |
| `before_checked_in` | 调用签到接口前的服务端状态。 |
| `after_checked_in` | 调用签到接口后的服务端状态。 |
| `reward` | 服务端返回的本次奖励。 |
| `balance_delta` | 前后余额差，仅作记录，不作为唯一成功依据。 |
| `response_balance` | 签到响应携带的余额。 |

## 结果码

| 结果码 | 成功 | 含义 |
| :--- | :---: | :--- |
| `CLAIMED` | 是 | 本次领取完成，奖励为正数，且签到后状态已翻转。 |
| `ALREADY_CLAIMED` | 是 | 运行前或响应中确认当日已签到。 |
| `AVAILABLE` | 是 | 查询模式确认当前可签到。 |
| `INACTIVE` | 否 | 站点没有报告可用的每日签到。 |
| `CLAIM_NOT_APPLIED` | 否 | 签到接口返回成功，但回读状态仍为 false。 |
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

## 成功判据

本项目不把“脚本跑了”“HTTP 200”“响应里有 `claimed`”单独当成成功。

| 场景 | 必须满足 |
| :--- | :--- |
| 今日新领取 | `claimed=true`、`reward>0`、签到后 `overview.checkin.checked_in=true` |
| 今日已领取 | 运行前 `overview.checkin.checked_in=true`，或响应明确 `checked_in=true` 且回读仍为 true |
| 查询模式 | 只读 `/api/overview`，不得调用签到接口 |

## 测试

```powershell
python -m unittest discover -s tests -v
python -m compileall -q .
python -m ruff check baipiao_daily.py tests
```

离线测试全部使用 fake response 和 fake session，不连接真实账号。

## 隐私

本仓库不包含账号、JWT、Cookie、手机号、邮箱、运行日志或真实响应。
不要把 `baipiao-report.json`、`baipiao-report.jsonl`、Cookie、JWT 或截图提交到仓库。

## 支持

脚本免费公开。如果它确实帮你省了时间，欢迎自愿赞赏。

<p align="center">
  <img src="assets/donate-wechat.png" width="260" alt="微信赞赏码" />
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="assets/donate-alipay.jpg" width="260" alt="支付宝收款码" />
</p>

> 收款码仅用于向作者自愿赞赏。任何第三方以代下载、代部署、内部版或会员群为由收费，均与作者无关。

## 免责声明

本项目用于个人学习和合法的个人自动化。Baipiao 的活动规则、接口、奖励和账号资格由服务方决定；使用前请确认对应服务条款，并自行承担接口变化和账号风险。

## 文件

```text
baipiao_daily.py
tests/test_baipiao_daily.py
.github/workflows/baipiao.yml
docs/README.en.md
docs/README.zh-Hant.md
docs/README.ja.md
docs/README.ko.md
docs/README.pt-BR.md
LICENSE
NOTICE.md
THIRD_PARTY_NOTICES.md
```
