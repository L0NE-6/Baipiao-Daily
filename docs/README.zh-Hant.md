# Baipiao Daily

[简体中文](../README.md) · [English](README.en.md) · **繁體中文** · [日本語](README.ja.md) · [한국어](README.ko.md) · [Português (BR)](README.pt-BR.md)

Baipiao 每日簽到，支援多帳號隔離、簽到前後狀態回讀與 JSONL 輸出。

## 流程

```text
GET /api/overview
  -> POST /api/checkin，Bearer bitapi_session，無 body
  -> 再次 GET /api/overview
```

只有同時符合以下條件才會回報 `CLAIMED`：

- 簽到回應 `claimed=true`；
- `reward>0`；
- 第二次回讀 `checkin.checked_in=true`。

## 憑證

多帳號環境變數 `BAIPIAO_ACCOUNTS`：

```text
備註|bitapi_session
```

單帳號使用 `BAIPIAO_SESSION`。第二欄可填 JWT，也可填包含
`bitapi_session` 的 Cookie 標頭。

## 執行

```powershell
python -m pip install -r requirements.txt
$env:BAIPIAO_SESSION = "<bitapi_session>"
python baipiao_daily.py
```

只查狀態：

```powershell
python baipiao_daily.py --query
```

只跑第二個帳號：

```powershell
python baipiao_daily.py --only 2
```

## 結果

| 結果 | 含義 |
| :--- | :--- |
| `CLAIMED` | 本次獎勵已確認，且回讀狀態已翻為 true。 |
| `ALREADY_CLAIMED` | 服務端確認今日已簽到。 |
| `AVAILABLE` | 查詢模式確認目前可簽到。 |
| `INACTIVE` | 站點沒有回報可用的每日簽到。 |
| `CLAIM_NOT_APPLIED` | 請求成功，但回讀仍為 false。 |
| `CREDIT_UNCONFIRMED` | 獎勵缺失或不是正數。 |
| `AUTH_EXPIRED` | `bitapi_session` 失效。 |
| `BLOCKED` | 返回 HTML 驗證頁。 |
| `CONFIG_ERROR` | 環境變數或基址錯誤。 |

## Actions

推送時執行測試；排程或手動執行時簽到並上傳 JSON 報告。請設定
`BAIPIAO_ACCOUNTS` 或 `BAIPIAO_SESSION` Secret。

## 測試

```powershell
python -m unittest discover -s tests -v
python -m compileall -q .
python -m ruff check baipiao_daily.py tests
```

全部測試使用假回應與假連線，不連接真實帳號。

## 隱私

不要提交 JWT、Cookie、報告、截圖或帳號資訊。腳本只輸出遮罩後的備註。

## 授權

MIT。請見 `LICENSE`、`NOTICE.md` 與 `THIRD_PARTY_NOTICES.md`。
