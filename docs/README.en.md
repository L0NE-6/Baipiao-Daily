# Baipiao Daily
[简体中文](../README.md) · **English** · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Português (BR)](README.pt-BR.md)
> Version: **v1.0.0** (2026-11-24)



Baipiao daily check-in with multi-account isolation and strict before/after
status readback.

## Flow

```text
GET /api/overview
  -> POST /api/checkin with Bearer bitapi_session and no body
  -> GET /api/overview again
```

The script only reports `CLAIMED` when the check-in response has
`claimed=true`, `reward>0`, and the second overview read has
`checkin.checked_in=true`.

## Credentials

Multi-account:

```text
label|bitapi_session
```

Set it as `BAIPIAO_ACCOUNTS`. A single account can use `BAIPIAO_SESSION`.

The second field may be the JWT itself or a Cookie header containing
`bitapi_session`.

## Run

```powershell
python -m pip install -r requirements.txt
$env:BAIPIAO_SESSION = "<bitapi_session>"
python baipiao_daily.py
```

Query only:

```powershell
python baipiao_daily.py --query
```

Select one account:

```powershell
python baipiao_daily.py --only 2
```

## Results

| Result | Meaning |
| :--- | :--- |
| `CLAIMED` | New reward confirmed and the overview state flipped to true. |
| `ALREADY_CLAIMED` | The server reports today's check-in was already recorded. |
| `AVAILABLE` | Query mode confirms the check-in is available. |
| `INACTIVE` | The portal reports no active daily check-in. |
| `CLAIM_NOT_APPLIED` | The request returned success but overview still says false. |
| `CREDIT_UNCONFIRMED` | Reward is missing or not positive. |
| `AUTH_EXPIRED` | `bitapi_session` is invalid or expired. |
| `BLOCKED` | The site returned an HTML challenge. |
| `CONFIG_ERROR` | Environment variables are missing or invalid. |

## Actions

The workflow runs tests on push and runs the check-in on schedule or manual
dispatch. Configure `BAIPIAO_ACCOUNTS` or `BAIPIAO_SESSION` as a repository
secret. Reports are uploaded as workflow artifacts.

## Test

```powershell
python -m unittest discover -s tests -v
python -m compileall -q .
python -m ruff check baipiao_daily.py tests
```

All tests use fake responses and fake sessions.

## Privacy

Do not commit JWTs, cookies, reports, screenshots, or account details. The
script only prints the masked account label.

## License

MIT. See `LICENSE`, `NOTICE.md`, and `THIRD_PARTY_NOTICES.md`.
